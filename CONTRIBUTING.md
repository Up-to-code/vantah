# Contributing to vAntah

vAntah is a custom desktop shell for Alpine Linux, maintained in public at https://github.com/Up-to-code/vantah. Its original code is MIT licensed. See LICENSE and the third-party licensing notes in README.md before redistributing themes or branding.

## Make a change

Fork the repository, create a branch, and keep each pull request focused on one problem. Include the observed problem, your change, and how you checked it. For desktop changes, include a real screenshot and state the display size, language, compositor and light/dark mode. Never include passwords, private documents or other personal desktop content in recordings.

## Run the checks

```sh
python3 -m compileall -q shell.py desktop_apps.py fix-vnc.py sandbox scripts
python3 sandbox/test-installer.py
find . -name '*.sh' -exec sh -n {} \;
```

The installer tests use temporary directories and fake Docker/curl commands. They check checksum failures, invalid ports and preservation of existing containers without building an image or changing your Docker containers.

GTK integration tests require a Linux desktop with PyGObject and GTK 3. Run `python3 sandbox/test-desktop-apps.py` inside the Alpine GUI session, with its D-Bus environment. For the running sandbox: `docker exec -u sandbox alpine-gui sh -c ' . /tmp/vantah-session.env; DISPLAY=:1 python3 /home/sandbox/.local/share/alpine-shell/sandbox/test-desktop-apps.py'`. Trash needs the session’s GVfs service. Test the actual patched noVNC client with the keyboard and sizing checks documented in README.md.

## Test desktop behavior

Check launcher search and keyboard navigation; launch and focus a real app; open Settings and Files; restore a disposable trashed file; switch English/Arabic and light/dark mode. Inspect glass and all four window corners with KWin enabled. UI source changes must receive a Rams quick review with `via=rules`; document a review service failure when the service is unavailable.

Use a separate container for a clean build. The current KWin image needs substantial build time, RAM and disk space. Do not describe a clean image, Raspberry Pi or old-PC installation as validated until it has actually booted and been checked.

## Report an issue

Use https://github.com/Up-to-code/vantah/issues and include the revision, CPU architecture, container/native setup, steps to reproduce, expected behavior and a screenshot or relevant log excerpt. Redact personal data.
