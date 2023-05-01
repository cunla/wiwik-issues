from datetime import datetime, date
from typing import List

import bleach
import pymdownx.arithmatex as arithmatex
from django import template
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe
from markdown import Markdown
from pymdownx import superfences

from forum.models import UserInput, Question, TagFollow
from tags.models import Tag
from userauth.models import ForumUser
from userauth.utils import user_most_active_tags
from wiwik_lib.utils import CURRENT_SITE

register = template.Library()

MARKDOWN_EXTENSIONS = [
    'nl2br',
    'toc',
    'pymdownx.magiclink',
    'pymdownx.extra',
    'pymdownx.emoji',
    'pymdownx.details',
    'pymdownx.keys',
    'pymdownx.superfences',
    'pymdownx.arithmatex',
]
MARKDOWN_EXTENSIONS_CONFIG = {
    "pymdownx.superfences": {
        "custom_fences": [
            {
                'name': 'mermaid',
                'class': 'mermaid',
                'format': superfences.fence_div_format,
            },
        ]
    },
}
if settings.LATEX_SUPPORT_ENABLED:
    MARKDOWN_EXTENSIONS_CONFIG["pymdownx.arithmatex"] = {
        'generic': True,
    }
    MARKDOWN_EXTENSIONS_CONFIG["pymdownx.superfences"]["custom_fences"].append({
        "name": "math",
        "class": "arithmatex",
        'format': arithmatex.fence_generic_format,
    })


@register.filter('startswith')
def startswith(text, starts):
    return isinstance(text, str) and text.startswith(starts)


markdown = Markdown(
    extensions=MARKDOWN_EXTENSIONS,
    extension_configs=MARKDOWN_EXTENSIONS_CONFIG
)

ALLOWED_ATTRIBUTES = {
    "div": ["class"],
    "a": ["href", "title"],
    "abbr": ["title"],
    "acronym": ["title"],
}
ALLOWED_TAGS = [
    'kbd',
    "h1", "h2", "h3", "h4", "h5", "h6",
    "b", "i", "strong", "em", "tt",
    "p", "br",
    "span", "div", "blockquote", "code", "pre", "hr",
    "ul", "ol", "li", "dd", "dt",
    "img",
    "a",
    "sub", "sup",
]


@register.filter(is_safe=True)
def markdownify(text: str):
    html = markdown.convert(text)
    html = bleach.clean(html, attributes=ALLOWED_ATTRIBUTES, tags=ALLOWED_TAGS)
    return mark_safe(html)


@register.filter(is_safe=True)
def absolute_datetime(value: datetime):
    return value.strftime('%Y-%m-%d at %H:%M') if value is not None else ''


@register.filter(is_safe=True)
def absolute_date(value: date):
    return value.strftime('%Y-%m-%d') if value is not None else ''


@register.filter(is_safe=True)
def humanize_number(value: int):
    if value is None:
        return ''
    if value > 1_000_000_000:
        return '{:,}B'.format((value // 100_000_000) / 10)
    if value > 1_000_000:
        return '{:,}m'.format((value // 100_000) / 10)
    if value > 1_000:
        return '{:,}k'.format((value // 100) / 10)
    return value


@register.simple_tag()
def share_link(u: UserInput):
    if isinstance(u, Question):
        link = f"{CURRENT_SITE}{reverse('forum:thread', args=[u.pk])}#question_{u.pk}"
    else:
        link = f"{CURRENT_SITE}{reverse('forum:thread', args=[u.question.pk])}#answer_{u.pk}"
    return mark_safe(link)


@register.filter(is_safe=True)
def tag_experts(tag: Tag) -> List[TagFollow]:
    """
    Returns list of 3 users with most reputation on the tag.

    The reason to use this method and not tag.experts property is because this
    method returns the TagFollow objects which have the user reputation for the tag.

    Args:
        tag (Tag): tag to search experts for

    Returns:
        List of up to 3 TagFollow objects with the most reputation.

    """
    return tag.tagfollow_set.filter(reputation__gt=0).order_by('-reputation')[:3]


@register.filter(is_safe=True)
def user_active_tags(u: ForumUser):
    return user_most_active_tags(u)


_3RD_PARTY_URLS = {
    'CDN': {
        'bootstrap-css': 'https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css',
        'bootstrap-js': 'https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.min.js',
        'bootstrap-bundle-js': 'https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js',
        'easymde-js': 'https://cdn.jsdelivr.net/npm/easymde@2.18.0/dist/easymde.min.js',
        'easymde-css': 'https://cdn.jsdelivr.net/npm/easymde@2.18.0/dist/easymde.min.css',
        'croppie-js': 'https://cdn.jsdelivr.net/npm/croppie@2.6.5/croppie.min.js',
        'croppie-css': 'https://cdn.jsdelivr.net/npm/croppie@2.6.5/croppie.css',
        'font-awesome-css': 'https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css',
        'tagify-js': 'https://cdn.jsdelivr.net/npm/@yaireo/tagify@4.17.8/dist/tagify.min.js',
        'tagify-polyfills-js': 'https://cdn.jsdelivr.net/npm/@yaireo/tagify@4.17.8/dist/tagify.polyfills.min.js',
        'mermaidjs': 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs',
    },
    'STATIC': {
        'bootstrap-css': 'bootstrap-5.2.3-dist/css/bootstrap.min.css',
        'bootstrap-js': 'bootstrap-5.2.3/dist/js/bootstrap.min.js',
        'bootstrap-bundle-js': 'bootstrap-5.2.3/dist/js/bootstrap.bundle.min.js',
        'easymde-js': 'easymde/easymde.min.js',
        'easymde-css': 'easymde/easymde.min.css',
        'croppie-js': 'croppie/croppie.min.js',
        'croppie-css': 'croppie/croppie.min.css',
        'font-awesome-css': 'css/font-awesome.min.css',
        'tagify-js': 'tagify/tagify.js',
        'tagify-polyfills-js': 'tagify/tagify.polyfills.min.js',
        'mermaidjs': 'mermaidjs/dist/mermaid.esm.min.mjs',
    },
}


@register.simple_tag(name='tool_url')
def get_url(tool_name: str):
    if tool_name not in _3RD_PARTY_URLS['CDN'] or tool_name not in _3RD_PARTY_URLS['STATIC']:
        raise template.TemplateSyntaxError(f'{tool_name} does not exist!')
    if settings.USE_CDN:
        return _3RD_PARTY_URLS['CDN'][tool_name]
    else:
        return static(_3RD_PARTY_URLS['STATIC'][tool_name])
