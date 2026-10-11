FROM alpine:3.24.2 AS glass-build
COPY sandbox/build-glass.sh sandbox/patch-kwin-x11.py /tmp/vantah-build/
RUN sh /tmp/vantah-build/build-glass.sh

FROM alpine:3.24.2
RUN apk add --no-cache xfce4 xfce4-terminal xvfb x11vnc novnc websockify dbus dbus-x11 font-dejavu adwaita-icon-theme mousepad py3-gobject3 py3-cairo libwnck3 xprop tzdata kwin breeze breeze-cursors mesa-dri-gallium mesa-gl qt6-qtsensors \
    && adduser -D -u 1000 sandbox \
    && mkdir -p /home/sandbox/.config/autostart /home/sandbox/.local/share/alpine-shell /workspace
COPY --from=glass-build /usr/bin/kwin_x11 /usr/bin/
COPY --from=glass-build /usr/lib/libkwin-x11.so* /usr/lib/
COPY --from=glass-build /usr/lib/qt6/plugins/kwin-x11/ /usr/lib/qt6/plugins/kwin-x11/
COPY --from=glass-build /usr/share/kwin-x11/ /usr/share/kwin-x11/
COPY --from=glass-build /usr/libexec/kwin_killer_helper_x11 /usr/libexec/
COPY --from=glass-build /usr/lib/qt6/qml/org/kde/kwin_x11/ /usr/lib/qt6/qml/org/kde/kwin_x11/
COPY --from=glass-build /usr/share/doc/vantah-glass/ /usr/share/doc/vantah-glass/
COPY . /home/sandbox/.local/share/alpine-shell/
COPY alpine-shell.desktop /home/sandbox/.config/autostart/
COPY sandbox/start-desktop.sh /usr/local/bin/start-desktop
RUN python3 /home/sandbox/.local/share/alpine-shell/fix-vnc.py \
    && chmod +x /usr/local/bin/start-desktop \
    && chown -R sandbox:sandbox /home/sandbox /workspace
USER sandbox
ENV DISPLAY=:1
WORKDIR /workspace
EXPOSE 6080
CMD ["/usr/local/bin/start-desktop"]
