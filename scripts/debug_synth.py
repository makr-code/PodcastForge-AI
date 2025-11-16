#!/usr/bin/env python3
"""Debug helper to call synthesize_script_preview and show return value."""
from podcastforge.integrations.script_orchestrator import synthesize_script_preview
from podcastforge.core.events import get_event_bus
import sys

# simple progress subscriber
def bus_print(evt):
    print("[BUS]", evt)

get_event_bus().subscribe('script.tts_progress', bus_print)
get_event_bus().subscribe('script.preview_ready', bus_print)

res = synthesize_script_preview('projects/example_podcast_project.yaml', 'out/debug', max_workers=2, on_progress=lambda *a: print('[CB]', a))
print('RESULT:', res)

get_event_bus().unsubscribe('script.tts_progress', bus_print)
get_event_bus().unsubscribe('script.preview_ready', bus_print)
