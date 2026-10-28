'use strict';
const fs = require('fs/promises');
const path = require('path');

function pythonPaths(sourceRoot, resourceRoot, platform = process.platform) {
  return platform === 'win32'
    ? {local: path.join(sourceRoot, '.venv', 'Scripts', 'python.exe'), bundled: path.join(resourceRoot, 'python', 'python.exe')}
    : {local: path.join(sourceRoot, '.venv', 'bin', 'python3'), bundled: path.join(resourceRoot, 'python', 'bin', 'python3')};
}

function steamRoots(env = process.env) {
  const home = env.HOME;
  if (!home) return [];
  return [path.join(home, '.steam', 'steam'), path.join(home, '.steam', 'root'),
    path.join(env.XDG_DATA_HOME || path.join(home, '.local', 'share'), 'Steam'),
    path.join(home, '.var', 'app', 'com.valvesoftware.Steam', '.local', 'share', 'Steam')];
}

// Proton runs the Windows executable. Its cmdline retains the executable argument;
// the launcher/Steam process mentioning the game in an environment variable does not count.
function gameArgument(args) {
  return args.find(arg => /(^|[\\/])Borderlands4(?:-Win64-Shipping)?\.exe$/i.test(arg));
}
function gameRootFromArgument(argument, cwd) {
  if (!argument) return '';
  let executable = argument.replaceAll('\\', '/');
  if (/^z:\//i.test(executable)) executable = executable.slice(2);
  else if (/^[a-z]:\//i.test(executable)) return ''; // Wine drive mapping is not guessed.
  if (!path.isAbsolute(executable)) executable = path.resolve(cwd, executable);
  const suffix = /\/OakGame\/Binaries\/Win64\/Borderlands4(?:-Win64-Shipping)?\.exe$/i;
  return suffix.test(executable) ? executable.replace(suffix, '') : '';
}

async function inspectGameProcesses({io = fs, procRoot = '/proc', uid = process.getuid?.()} = {}) {
  const processes = [];
  let queryFailed = false;
  let names;
  try { names = await io.readdir(procRoot); } catch { return {processes, queryFailed:true}; }
  for (const pid of names.filter(name => /^\d+$/.test(name))) {
    const folder = path.join(procRoot, pid);
    try {
      const stat = await io.stat(folder);
      if (uid !== undefined && stat.uid !== uid) continue;
      const args = (await io.readFile(path.join(folder, 'cmdline'), 'utf8')).split('\0').filter(Boolean);
      const argument = gameArgument(args);
      if (!argument) continue;
      let gameRoot = '';
      try { gameRoot = gameRootFromArgument(argument, await io.readlink(path.join(folder, 'cwd'))); }
      catch { /* A known game process still blocks installation without its path. */ }
      processes.push({pid:Number(pid), gameRoot});
    } catch (error) {
      if (error.code !== 'ENOENT' && error.code !== 'ESRCH') queryFailed = true;
    }
  }
  return {processes, queryFailed};
}
function replaySaveRoot(env = process.env) {
  if (!env.MSBT_SAVE_ROOT || !path.isAbsolute(env.MSBT_SAVE_ROOT))
    throw Error('Linux save replay needs MSBT_SAVE_ROOT set to the absolute Proton Borderlands 4 Saved/SaveGames folder. No host Documents folder is substituted.');
  return env.MSBT_SAVE_ROOT;
}
module.exports = {replaySaveRoot, pythonPaths, steamRoots, gameArgument, gameRootFromArgument, inspectGameProcesses};
