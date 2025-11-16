"""Demo: use orchestrator to create a chapter/paragraph plan for a podcast.

This script demonstrates the intended workflow: extract chapters, split
into paragraphs and produce a plan describing how TTS should be invoked.
"""
from pathlib import Path
from podcastforge.integrations.ebook2audiobook import orchestrator
import sys


def main():
    sample = Path('examples/sample.epub')
    if not sample.exists():
        print('No examples/sample.epub found — create a sample or point to an epub file.')
        sys.exit(0)

    res = orchestrator.generate_podcast_from_ebook(str(sample), 'output', per_paragraph=True, dry_run=True)
    print('Plan OK:', res.get('ok'))
    print('Message:', res.get('message'))
    print('Chapters found:', len(res.get('plan', [])))
    for p in res.get('plan', [])[:5]:
        print('-', p)


if __name__ == '__main__':
    main()
