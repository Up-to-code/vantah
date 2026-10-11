# Release checks: 0.2.1 preview

Checked on 11 October 2026 against the current source and running ARM64 Alpine sandbox.

- Eight installer regression tests passed, including corrupt downloads, port validation and existing-container preservation.
- All Python modules compiled and all shell scripts passed `sh -n`.
- Both native desktop integration tests passed in the existing session: Files filtering, Arabic filename Trash/restore, and Arabic Settings layout. The session D-Bus environment is required for GVfs Trash; an invocation without it failed to enumerate Trash and was corrected to use `/tmp/vantah-session.env`.
- The subtitled English export is 15 seconds, 1080×1920, 30 fps, 450 frames. Full decoding passed. All five subtitle cards occupy consecutive three-second intervals. The export is silent for independent music selection.

The release updates documentation, contributor instructions, CI and downloadable media. No UI source changed. A fresh build of the revised KWin container, x86_64/old-PC installation, Raspberry Pi hardware and robotics remain unvalidated. The live sandbox checks do not establish these results.
