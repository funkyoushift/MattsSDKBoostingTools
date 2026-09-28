import {betterAuth} from 'better-auth';
export function authOptions(env) {
  if(!env.AUTH_SECRET || env.AUTH_SECRET.length<32 || !env.PUBLIC_ORIGIN) throw Error('Developer sign-in has not been configured.');
  return {
    database:env.LIBRARY, secret:env.AUTH_SECRET, baseURL:env.PUBLIC_ORIGIN,
    trustedOrigins:[env.PUBLIC_ORIGIN],
    emailAndPassword:{enabled:true,minPasswordLength:12,maxPasswordLength:128,revokeSessionsOnPasswordReset:true},
    session:{expiresIn:60*60*8,updateAge:60*30,cookieCache:{enabled:false}},
    rateLimit:{enabled:true,storage:'database',window:60,max:60},
    advanced:{ipAddress:{ipAddressHeaders:['cf-connecting-ip']},useSecureCookies:env.PUBLIC_ORIGIN.startsWith('https:')},
    logger:{level:'error'}
  };
}
export const createAuth=env=>betterAuth(authOptions(env));
export async function identity(request,env) {
  const session=await createAuth(env).api.getSession({headers:request.headers});
  if(!session)return null;
  const member=await env.LIBRARY.prepare('SELECT role FROM team WHERE user_id=?').bind(session.user.id).first();
  return {id:session.user.id,name:session.user.name,email:session.user.email,role:member?.role||'member'};
}
export const permissions={member:[],reviewer:['review'],editor:['review','edit'],admin:['review','edit','delete'],owner:['review','edit','delete','team']};
export const allowed=(person,action)=>Boolean(person&&permissions[person.role]?.includes(action));
