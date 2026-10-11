"""Generate vAntah's compact, editable dark-tile dock icons."""
from pathlib import Path

symbols = {
    'trash': '''<path d="M13 17H51L47 51Q46 56 41 56H23Q18 56 17 51Z" fill="#60646a" fill-opacity=".4" stroke="#bfc4ce" stroke-width="1.5"/><ellipse cx="32" cy="17" rx="19" ry="4" fill="#303237" stroke="#e3e5ea" stroke-width="1.5"/><path d="M20 26L23 48M32 27V49M44 26L41 48" stroke="#ffffff" stroke-opacity=".1" stroke-width="2"/>''',
    'files': '''<path d="M8 22V16Q8 11 13 11H27L33 18H51Q56 18 56 23V49Q56 54 51 54H13Q8 54 8 49Z" fill="url(#blue)"/>
<path d="M8 26H56V49Q56 54 51 54H13Q8 54 8 49Z" fill="#17c7fa"/>
<path d="M10 27H54" stroke="#7ce8ff" stroke-width="2" stroke-opacity=".65"/>
<path d="M23 36H42M23 42H38" stroke="#07537c" stroke-width="3" stroke-linecap="round"/>''',
    'terminal': '''<path d="M14 19L29 31L14 43" fill="none" stroke="#f5f6f8" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M35 46H51" stroke="#b9bcc3" stroke-width="4" stroke-linecap="round"/>''',
    'editor': '''<rect x="12" y="9" width="35" height="46" rx="6" fill="#f0f4fa"/>
<path d="M19 20H39M19 28H39M19 36H34M19 44H29" stroke="#9aabc4" stroke-width="2.3" stroke-linecap="round"/>
<path d="M32 43L48 12Q49 10 51 11L56 14Q58 15 57 17L41 48L31 54Z" fill="url(#blue)" stroke="#b1edff" stroke-width="1.2"/>
<path d="M31 54L33 44L41 48Z" fill="#20354e"/>''',
    'settings': '''<g stroke="#d4d8e0" stroke-width="3.5" stroke-linecap="round"><path d="M10 17H54M10 32H54M10 47H54"/></g>
<g fill="#f7f8fc" stroke="#6d7582" stroke-width="1.5"><circle cx="24" cy="17" r="6"/><circle cx="43" cy="32" r="6"/><circle cx="21" cy="47" r="6"/></g>''',
    'applications': ''.join(
        f'<rect x="{10+column*16}" y="{10+row*16}" width="12" height="12" rx="3.5" fill="{color}"/>'
        for (row, column), color in zip(
            ((row, column) for row in range(3) for column in range(3)),
            ['#27c8fa', '#b697ff', '#ffbf53', '#3edc94', '#588fff', '#ff718d', '#db9cff', '#ffd565', '#64dde9'])),
}
for name, symbol in symbols.items():
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" role="img" aria-label="{name.title()}">
<defs>
<linearGradient id="tile" x2="0" y2="1"><stop stop-color="#282a2d"/><stop offset="1" stop-color="#101113"/></linearGradient>
<linearGradient id="blue" x2="0" y2="1"><stop stop-color="#5cdfff"/><stop offset="1" stop-color="#078bdc"/></linearGradient>
</defs>
<rect x="1" y="1" width="62" height="62" rx="16" fill="url(#tile)" stroke="#ffffff" stroke-opacity=".12"/>
<path d="M17 2H47Q62 2 62 17" fill="none" stroke="#ffffff" stroke-opacity=".08"/>
{symbol}
</svg>'''
    Path(__file__).with_name(f'{name}.svg').write_text(svg)
