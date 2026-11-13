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
