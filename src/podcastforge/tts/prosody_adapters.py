"""Prosody adapter utilities.

Convert generic prosody dicts ({'rate', 'pitch_cents', 'energy'}) into
engine-specific kwargs. These adapters are intentionally conservative — they
only map fields that are commonly supported and leave the rest alone.
"""
from typing import Dict, Optional


def adapt_for_engine(engine_name: Optional[str], prosody: Optional[Dict]) -> Dict:
    """Return adapted kwargs for `engine.synthesize(**kwargs)` based on engine.

    engine_name may be an enum-like name (e.g. 'PIPER' or 'BARK') or None.
    """
    out = {}
    if not prosody or not isinstance(prosody, dict):
        return out

    rate = prosody.get('rate')
    pitch = prosody.get('pitch_cents')
    energy = prosody.get('energy')

    name = (engine_name.name if hasattr(engine_name, 'name') else (str(engine_name) if engine_name is not None else '')).upper()

    # Piper: map 'rate' -> 'length_scale' (inverse of speed), 'pitch_cents' -> 'pitch_shift'
    if 'PIPER' in name:
        # Interpret `rate` as speed multiplier: 1.0 = normal, >1 faster, <1 slower.
        # Piper's typical parameter is `length_scale` where >1 slows (longer), so
        # we invert rate -> length_scale := clamp(1.0 / rate, 0.5, 2.0)
        if rate is not None:
            try:
                r = float(rate)
                if r <= 0:
                    r = 1.0
                ls = 1.0 / r
                ls = max(0.5, min(2.0, ls))
                out['length_scale'] = ls
            except Exception:
                pass
        if pitch is not None:
            # piper pitch shift in cents
            try:
                out['pitch_shift_cents'] = float(pitch)
            except Exception:
                pass
        if energy is not None:
            try:
                # normalize energy to reasonable range 0.5..1.5
                e = float(energy)
                e = max(0.0, min(2.0, e))
                out['energy'] = e
            except Exception:
                pass

    # Bark / similar: map to 'tempo', 'pitch' names
    elif 'BARK' in name or 'XTTS' in name:
        # For these engines, tempo maps directly to speed multiplier
        if rate is not None:
            try:
                rt = float(rate)
                rt = max(0.5, min(2.0, rt))
                out['tempo'] = rt
            except Exception:
                pass
        if pitch is not None:
            try:
                out['pitch_cents'] = float(pitch)
            except Exception:
                pass
        if energy is not None:
            try:
                e = float(energy)
                e = max(0.0, min(2.0, e))
                out['energy'] = e
            except Exception:
                pass

    else:
        # Generic conservative mapping: provide keys that engine managers may accept
        if rate is not None:
            try:
                r = float(rate)
                out['rate'] = max(0.5, min(2.0, r))
            except Exception:
                pass
        if pitch is not None:
            try:
                out['pitch_cents'] = float(pitch)
            except Exception:
                pass
        if energy is not None:
            try:
                e = float(energy)
                out['energy'] = max(0.0, min(2.0, e))
            except Exception:
                pass

    return out
