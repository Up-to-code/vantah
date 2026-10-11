"""Render Alpine Shell's original glass icon set as editable SVG assets."""
from pathlib import Path

icons = {
    'files': ('#78d4ff', '#1479df', '<path d="M12 25V19Q12 15 16 15H27L32 21H49Q53 21 53 25V45Q53 49 49 49H16Q12 49 12 45Z" fill="#a9e6ff"/><path d="M12 28Q12 25 16 25H49Q53 25 53 29V45Q53 49 49 49H16Q12 49 12 45Z" fill="#e0f6ff" fill-opacity=".72" stroke="white" stroke-opacity=".7"/><path d="M22 36H44" stroke="#167ed3" stroke-width="2" stroke-linecap="round"/>'),
    'terminal': ('#606b82', '#101728', '<rect x="11" y="14" width="42" height="36" rx="7" fill="#111b30" fill-opacity=".72" stroke="#b6c9e8" stroke-opacity=".5"/><circle cx="17" cy="20" r="1.5" fill="#fa8290"/><circle cx="22" cy="20" r="1.5" fill="#fbd58d"/><circle cx="27" cy="20" r="1.5" fill="#88e5b3"/><path d="M19 29L26 35L19 41M31 42H42" fill="none" stroke="#f4f8ff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'),
    'editor': ('#eef4ff', '#86a7da', '<rect x="17" y="12" width="30" height="42" rx="5" fill="#fff" fill-opacity=".87" stroke="white"/><path d="M23 23H40M23 30H38M23 37H35M23 44H32" stroke="#90a7c9" stroke-width="2" stroke-linecap="round"/><path d="M36 42L48 20L53 23L41 45L35 49Z" fill="#4e8deb" stroke="#e4efff" stroke-width="1.2"/>'),
    'settings': ('#b5c3e7', '#536ca7', '<g stroke="#f3f7ff" stroke-width="3" stroke-linecap="round"><path d="M16 21H48M16 32H48M16 43H48"/></g><g fill="#d7e7ff" stroke="#41618f" stroke-width="1.3"><circle cx="25" cy="21" r="4.5"/><circle cx="40" cy="32" r="4.5"/><circle cx="28" cy="43" r="4.5"/></g>'),
    'applications': ('#bfa9ff', '#6150ce', ''.join(f'<rect x="{x}" y="{y}" width="10" height="10" rx="3" fill="{color}" stroke="white" stroke-opacity=".55"/>' for x, y, color in [(14,14,'#bde8ff'),(27,14,'#e6c4ff'),(40,14,'#ffe1b5'),(14,27,'#b7f1d4'),(27,27,'#cbd9ff'),(40,27,'#ffccd5'),(14,40,'#e1ccff'),(27,40,'#ffe2b4'),(40,40,'#c7eeff')]))
}
for name, (top, bottom, symbol) in icons.items():
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
<defs><linearGradient id="base" x2="0" y2="1"><stop stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>
<linearGradient id="shine" x2="0" y2="1"><stop stop-color="white" stop-opacity=".47"/><stop offset="1" stop-color="white" stop-opacity="0"/></linearGradient></defs>
<rect x="2" y="3" width="60" height="60" rx="16" fill="#000" fill-opacity=".17"/>
<rect x="2" y="1" width="60" height="60" rx="16" fill="url(#base)" stroke="white" stroke-opacity=".44"/>
<path d="M3 24V17Q3 2 18 2H46Q61 2 61 17V24Q33 35 3 24Z" fill="url(#shine)"/>
{symbol}</svg>'''
    Path(__file__).with_name(f'{name}.svg').write_text(svg)
