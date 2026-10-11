FROM alpine:3.24.2
RUN apk add --no-cache xfce4 xfce4-terminal tigervnc novnc websockify dbus dbus-x11 font-dejavu adwaita-icon-theme mousepad py3-gobject3 py3-cairo libwnck3 xprop tzdata picom \
    && adduser -D -u 1000 sandbox \
    && mkdir -p /home/sandbox/.config/autostart /home/sandbox/.local/share/alpine-shell /workspace
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
