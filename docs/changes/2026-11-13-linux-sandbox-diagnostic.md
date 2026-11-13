# Linux sandbox CI diagnosis - 2026-11-13

Candidate a2cbdb7b failed Ubuntu 26.04.1 AppImage smoke in run 43502920907:
Chromium rejected its SUID sandbox helper before startup. The same failure was
recorded for 2.41.2 in run 43302963095. Host sysctls alone do not prove why the
namespace sandbox was unavailable; AppArmor denial remains a hypothesis.

This isolated diagnostic branch adds tools/diagnose_linux_sandbox.sh and one
failure-only workflow step/upload path. It records helper ownership/mode, mount
options, namespace probe, AppArmor status and kernel messages around a repeat
of unchanged extracted AppRun smoke. It preserves the failed verification receipt.
No runtime, gate criteria, security settings, versions or release assets change.
The temporary scratch installation exists only on the disposable CI runner.

Validation: workflow YAML parse and shell syntax checks are run before dispatch;
actual native result will be appended after the diagnostic job. This does not
establish live BL4/Proton qualification. No desktop/game control is involved.
Rollback is reverting this diagnostic-only commit; primary candidate remains
untouched. No blanket no-sandbox, helper chmod/chown or host-policy workaround
is attempted. Supported affected-host startup remains unresolved pending evidence.

## Native diagnostic result

Diagnostic commit 01d87ac20605310154412e4d0ba3d469f6bbc4b1 ran in CI
43506646620 on Ubuntu 26.04.1. Linux packaging/source checks passed, smoke failed,
and failure-only diagnostics completed successfully. Bash syntax, YAML parsing
and diff checks passed locally before dispatch. Windows remained in progress
when Linux evidence was collected; this run is not a passing release gate.

The kernel audit records the original verifier executable PID 2712 transitioning
from unconfined to unprivileged_userns during userns_create, followed by child
2723 denied capability sys_admin. The diagnostic repeat PID 2776/child 2787
records the same sequence and smoke exit 133. Generic unshare also failed with
uid_map EPERM and the same capability denial. AppArmor involvement on this host
is therefore directly evidenced, rather than merely inferred from sysctls.
The extracted chrome-sandbox was UID/GID 1001, mode 755; the filesystem had no
nosuid mount flag. Relevant sandbox environment overrides were unset.

Evidence is in CI's linux-verification-evidence artifact, copied locally to
local/updater-repair/ci-26-diagnosis/run-43506646620/sandbox-diagnostics relative
to the primary workspace: kernel.txt, files.txt, host.txt, smoke.txt and exit
receipts. Both original and repeat executable paths/PIDs are in kernel.txt.
The source/runtime remains byte-identical to a2cbdb7b outside diagnostic tooling
and notes. No supported host-policy fix or game qualification is established;
do not reinterpret this diagnostic run or older-host success as a release pass.
