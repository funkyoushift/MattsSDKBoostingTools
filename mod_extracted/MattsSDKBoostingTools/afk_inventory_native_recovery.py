"""Tick-driven inventory recovery with bounded read retries and missing-item repair."""
import time
from collections import Counter
from .afk_inventory_capture import Capture
from .afk_inventory_recovery import item_counts


class NativeAdapter:
    def __init__(self, game, player, world, *, allow_afk=False, open_rewards=False):
        self.game, self.player, self.world = game, player, world
        self.allow_afk, self.open_rewards = allow_afk, open_rewards

    def target(self):
        world, rows = self.game.roster()
        row = next((row for row in rows if row['token'] == self.player), None)
        if world != self.world or row is None or not row['ready']:
            raise RuntimeError('Original guest is no longer ready in this world')
        return row

    def preflight(self, original):
        a = self.game.backend()
        if not original['rows']:
            return {'ok':False,'message':'An empty capture cannot prove the guest inventory is loaded; nothing cleared'}
        if not self.game.is_host() or (a.afk_lobby_status()['enabled'] and not self.allow_afk):
            return {'ok':False, 'message':'Host the game and stop AFK before the recovery test'}
        if any(r['quantity'] != 1 for r in original['rows']):
            return {'ok':False, 'message':'Stacked-item restoration is not yet verified; nothing cleared'}
        if a.serial_rewards._serial_delivery_busy() or a.complete_challenges_status()['active'] or a.uvh_boost_status()['active']:
            if not hasattr(self, '_preflight_deadline'):
                self._preflight_deadline = time.monotonic() + 60
            return {'ok':False, 'retry':time.monotonic() < self._preflight_deadline,
                    'message':'Waiting for existing boosts and deliveries to finish'}
        self.target()
        return {'ok':True}

    def begin(self, operation, record, player, world):
        self.target()
        token = {'operation':operation, 'record':record, 'deadline':time.monotonic()+300}
        if operation == 'clear':
            token['capture'] = Capture(player)
            token['phase'] = 'before_clear'
            if self.open_rewards:
                token['open_before_clear'] = True
                token['open_deadline'] = time.monotonic()+30
        elif operation in ('deliver','restore'):
            serials = list(record['delivery_serials'])
            if operation == 'restore':
                # Some game builds may retain equipped rows. Return only the
                # missing original copies, never duplicate retained originals.
                needed = item_counts(record['original']) - item_counts(record['retained'])
                serials = list(needed.elements())
            token['serials'] = serials
            if serials:
                rewards = self.game.backend().serial_rewards
                if rewards._serial_delivery_busy():
                    raise RuntimeError('Another delivery started; recovery will not replace it')
                row = self.target()
                rewards._do_give_serial_to_player_indices(serials,[row['index']],
                    scope_label='Inventory recovery test',mode='selected',bulk_authorized=True)
                seq = rewards._pending_serial_delivery_sequences[-1]
                seq['afk_player_state'] = player
                seq['post_open_delay'] = max(float(seq.get('post_open_delay',0)),3.0)
                token['sequence'] = seq
            token['settle_until'] = time.monotonic()+3
        else:
            token['capture'] = Capture(player)
        return token

    def retry_capture(self, token, player):
        if token.get('read_retries', 0) >= 5:
            return False
        token['read_retries'] = token.get('read_retries', 0) + 1
        token['capture'] = Capture(player)
        token['settle_until'] = time.monotonic() + 2
        return True

    def poll(self, token, player, world):
        row = self.target()
        if time.monotonic() > token['deadline']:
            return {'ok':False, 'nothing_cleared':token['operation'] == 'clear' and not token.get('clear_attempted'),
                    'delivery_finished':token.get('delivery_finished') is True,
                    'message':'Recovery timed out; backup retained and kick blocked'}
        operation = token['operation']
        if token.get('open_before_clear'):
            now = time.monotonic()
            if now < token.get('open_retry_after', 0):
                return None
            opened = self.game.backend().serial_rewards._open_target_reward_packages([row['index']])
            if opened != 1:
                if now >= token['open_deadline']:
                    return {'ok':False, 'nothing_cleared':True,
                            'message':'Guest reward manager unavailable; cleanup skipped before deletion'}
                token['open_retry_after'] = now+2
                return None
            token.pop('open_before_clear')
            token['settle_until'] = now+5
            return None
        if operation == 'verify' and self.game.backend().serial_rewards._serial_delivery_busy():
            # Captures taken during an unrelated or timed-out send are stale.
            token['capture'] = Capture(player)
            token['settle_until'] = time.monotonic() + 5
            return None
        if operation == 'verify' and 'repair_sequence' in token:
            rewards = self.game.backend().serial_rewards
            seq = token['repair_sequence']
            if any(s is seq for s in rewards._pending_serial_delivery_sequences):
                return None
            # Even interrupted sends are recaptured, never blindly replayed.
            token.pop('repair_sequence')
            token['capture'] = Capture(player)
            token['settle_until'] = time.monotonic() + 5
        if operation in ('deliver','restore'):
            seq = token.get('sequence')
            if seq is not None:
                rewards = self.game.backend().serial_rewards
                if any(s is seq for s in rewards._pending_serial_delivery_sequences):
                    return None
                if seq.get('afk_error') or seq.get('index',0) < len(seq['chunks']):
                    return {'ok':False, 'message':'Recovery delivery was interrupted; backup retained'}
                token.pop('sequence')
                token['delivery_finished'] = True
                token['settle_until'] = time.monotonic()+3
            if time.monotonic() < token['settle_until']:
                return None
            if operation == 'restore':
                return {'ok':True}
            if not token['serials']:
                return {'ok':True,'snapshot':{'ok':True,'phase':'complete','rows':[]}}
            token.setdefault('capture',Capture(player))
        if time.monotonic() < token.get('settle_until',0):
            return None
        capture = token['capture']
        status = capture.step(player)
        if not status['done']:
            return None
        if not status['ok']:
            if operation == 'clear' and token['phase'] == 'after_clear':
                # The clear call succeeded but emptied native slots may no
                # longer decode. Recovery must still return the originals.
                # Final duplicate-preserving verification decides success.
                return {'ok':True,'snapshot':None,'clear_submitted':True,
                        'readback_error':status['error']}
            if self.retry_capture(token, player):
                return None
            return {'ok':False,'nothing_cleared':operation == 'clear' and not token.get('clear_attempted'),
                    'delivery_finished':token.get('delivery_finished') is True,
                    'message':status['error']}
        snapshot = capture.snapshot()
        if operation == 'clear' and token['phase'] == 'before_clear':
            if item_counts(token['record']['original']) - item_counts(snapshot):
                return {'ok':False,'nothing_cleared':True,'message':'Original items changed before clear; nothing deleted'}
            a = self.game.backend()
            if ((a.afk_lobby_status()['enabled'] and not self.allow_afk) or a.serial_rewards._serial_delivery_busy()
                    or a.complete_challenges_status()['active'] or a.uvh_boost_status()['active']):
                if self.retry_capture(token, player):
                    return None
                return {'ok':False,'nothing_cleared':True,'message':'Another operation started; nothing deleted'}
            token['clear_attempted'] = True
            message = a.streamer_chaos.empty_backpack_for_pc(row['pc'])
            if not a.streamer_chaos.result_ok(str(message)):
                return {'ok':False,'message':str(message)}
            token['phase'] = 'after_clear'
            token['capture'] = Capture(player)
            token['settle_until'] = time.monotonic()+3
            return None
        if operation == 'deliver':
            # Subtract retained originals by exact observed IDs, preserving
            # duplicate new serials in the intentional delivery snapshot.
            retained = {(r['handle'],r['instance_id']) for r in token['record']['retained']['rows']}
            snapshot['rows'] = [r for r in snapshot['rows'] if (r['handle'],r['instance_id']) not in retained]
        if operation == 'verify' and token['record'].get('restore_metadata') is False:
            expected = item_counts(token['record']['original']) + Counter(token['record']['delivery_serials'])
            actual = item_counts(snapshot)
            missing = expected - actual
            if missing and not (actual - expected):
                # A changed serial representation can look both missing and
                # unexpected. Never resend that ambiguous inventory as a deficit.
                # Require a second stable capture after settling before sending
                # a deficit. Late replication must not produce duplicate gear.
                if token.get('confirmed_missing') != missing:
                    token['confirmed_missing'] = missing
                    token['capture'] = Capture(player)
                    token['settle_until'] = time.monotonic() + 5
                    return None
                rewards = self.game.backend().serial_rewards
                if rewards._serial_delivery_busy():
                    token['capture'] = Capture(player)
                    token['settle_until'] = time.monotonic() + 2
                    return None
                if token.get('repair_attempts', 0) < 3:
                    token['repair_attempts'] = token.get('repair_attempts', 0) + 1
                    token.pop('confirmed_missing', None)
                    rewards._do_give_serial_to_player_indices(list(missing.elements()),[row['index']],
                        scope_label='Inventory recovery retry',mode='selected',bulk_authorized=True)
                    seq = rewards._pending_serial_delivery_sequences[-1]
                    seq['afk_player_state'] = player
                    seq['post_open_delay'] = max(float(seq.get('post_open_delay',0)),3.0)
                    token['repair_sequence'] = seq
                    return None
            return {'ok':True,'snapshot':snapshot,'delivery_reconciled':actual == expected,
                    'repair_attempts':token.get('repair_attempts', 0)}
        return {'ok':True,'snapshot':snapshot}
