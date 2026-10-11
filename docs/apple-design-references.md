# Apple 27 appearance references

Collected and inspected on 2026-10-11. The goal is closer visual alignment for
vAntah's Linux shell. This is not a verified pixel-perfect reproduction.
Apple images are linked as references, not bundled as theme artwork.

## Official source catalog

| Reference | Use |
| --- | --- |
| [Apple Design Resources](https://developer.apple.com/design/resources/) | Official macOS 27 and iOS/iPadOS 27 kits, icon templates, Siri resources |
| [Design kit announcement](https://developer.apple.com/news/?id=e2lxw9l1) | June 2026 kit versions and dark-mode components |
| [macOS 27 UI kit](https://www.figma.com/community/file/1651309434229735362/macos-27) | Component geometry; linked from Apple; full Figma document was not inspected |
| [iOS/iPadOS 27 UI kit](https://www.figma.com/community/file/1651309003795292092/ios-and-ipados-27) | Mobile component reference; full Figma document was not inspected |
| [macOS kit preview](https://developer.apple.com/design/resources/images/thumbnails/Thumbnail-UIKit-macOS27_2x.png) | Visually inspected grouped settings, rounded cards, compact controls |
| [iOS kit preview](https://developer.apple.com/design/resources/images/thumbnails/Thumbnail-UIKit-iOS27_2x.png?3=) | Visually inspected colored icons, translucent dock and tablet controls |
| [macOS 27 overview](https://www.apple.com/os/macos/) | Official screenshots, Siri/Spotlight and refined Liquid Glass |
| [iOS 27 overview](https://www.apple.com/os/ios/) | Official iPhone UI, icons and Siri examples |
| [Glass toolbar close-up](https://images.apple.com/v/os/g/images/macos/highlights/liquid_glass__bf6kssw93vrm_large.jpg) | Visually inspected grouped toolbar buttons, restrained borders and legible glyphs |
| [Siri conversation panel](https://images.apple.com/v/os/g/images/macos/siri/conversation__puy86qxwfayy_large.jpg) | Visually inspected dark floating panel, compact actions and input placement |
| [Siri desktop app](https://images.apple.com/v/os/g/images/macos/siri/siri_app__bf82k75xd8z6_large.jpg) | Visually inspected light window, traffic lights, translucent sidebar and bottom input |
| [Siri icon resource](https://devimages-cdn.apple.com/design/resources/download/Icon-Siri.dmg) | Official Apple download, located but not extracted or installed |
| [WWDC26 platform presentation](https://developer.apple.com/videos/play/wwdc2026/112/) | Readability and consistency refinements |
| [Icon Composer lab](https://developer.apple.com/videos/play/wwdc2026/8012/) | Layered icon design, material and contrast reference |

## Findings applied

The inspected Apple screenshots use recognizable colored artwork, not a uniform
black tile behind every app. Thin borders, soft backdrop blur and controlled
highlights support readable controls. Content regions are more solid than glass
navigation surfaces. Light and dark appearances change controls and window frames,
not just the wallpaper. Siri's conversation view and Spotlight's app search serve
different purposes; vAntah currently provides local application search only.

vAntah now uses a pinned open-source Linux package for app/system icons and
cursors, MacTahoe GTK controls and Aurorae traffic-light window frames. KWin Glass
has a narrower refraction edge, less color fringing, a quieter glow and stronger
backdrop blur. Search surfaces receive a more neutral tint to protect label contrast.

## Installed Linux packages and attribution

| Package | Pinned source revision | License |
| --- | --- | --- |
| [MacTahoe icons](https://github.com/vinceliuice/MacTahoe-icon-theme) | `839848b9a8a38a92a6936e30c4abe35cc6f2546d` | GPL-3.0 |
| [MacTahoe GTK](https://github.com/vinceliuice/MacTahoe-gtk-theme) | `1e45e19f510edb8cde18fa84d6cd5319f60b086b` | MIT |
| [MacTahoe KDE](https://github.com/vinceliuice/MacTahoe-kde) | `cbf6a1f71b591d143184855d62f6272ce533e7c3` | LGPL-3.0 |

These projects target macOS Tahoe-inspired Linux appearance. They are not official
Apple icon packages and do not supply Apple's layered Icon Composer rendering.

## Fidelity limits

There is no measured pixel-diff validation against a full macOS 27 component kit.
The official public previews were inspected; Figma's full documents were not
accessible through the research fetcher. GTK apps retain their own layouts and
menus. Inter is used rather than Apple's SF Pro. X11 KWin Glass provides live
blur and convex refraction, but newer Wayland-only glass controls are unavailable.
Software rendering and noVNC scaling affect animation smoothness and perceived
sharpness. No Siri service, voice assistant or Apple Intelligence backend is
implemented. Further exact matching requires component-by-component measurements,
not stronger claims about this theme package.
