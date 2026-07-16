"""Keyword lexicons for cinematic prompt understanding (no mocks)."""

from __future__ import annotations

# Production categories supported by RTAS Studio AI
CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Music Video": ("music video", "mv ", "mv,", "performance video", "lyrics video"),
    "Advertisement": ("advertisement", "commercial", "ad campaign", "promo ad", "brand ad"),
    "Movie Scene": ("movie scene", "film scene", "cinematic scene", "feature film"),
    "Documentary": ("documentary", "docu", "interview vérité", "observational"),
    "Islamic Video": ("islamic", "muslim", "mosque", "quran", "ramadan", "hajj", "nasheed"),
    "Podcast": ("podcast", "talk show", "host interview", "episode intro"),
    "Product Video": ("product video", "product demo", "unboxing", "sku", "product shot"),
    "Anime": ("anime", "manga", "cel shaded", "japanese animation"),
    "3D Animation": ("3d animation", "cgi animation", "blender", "pixar-like", "3d render"),
    "Talking Avatar": ("talking avatar", "digital human", "avatar presenter", "virtual host"),
    "Short Film": ("short film", "short movie", "indie short"),
    "Trailer": ("trailer", "teaser trailer", "movie trailer"),
    "YouTube Shorts": ("youtube short", "yt short", "shorts"),
    "TikTok": ("tiktok", "tik tok"),
    "Instagram Reel": ("instagram reel", "ig reel", "reels"),
}

TIME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Night": ("at night", "nighttime", "midnight", "moonlight", "night "),
    "Golden Hour": ("golden hour", "sunset", "dusk", "magic hour"),
    "Dawn": ("dawn", "sunrise", "daybreak", "first light"),
    "Day": ("daytime", "afternoon", "midday", "noon", "bright day"),
    "Blue Hour": ("blue hour", "twilight"),
}

WEATHER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Rain": ("rain", "rainfall", "downpour", "storm", "drizzle", "wet"),
    "Snow": ("snow", "blizzard", "snowfall"),
    "Fog": ("fog", "mist", "haze"),
    "Clear": ("clear sky", "sunny", "cloudless"),
    "Overcast": ("overcast", "cloudy", "grey sky", "gray sky"),
    "Wind": ("windy", "gale", "strong wind"),
}

EMOTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Sad": ("sad", "sorrow", "grief", "heartbroken", "tear"),
    "Lonely": ("alone", "lonely", "solitude", "isolated", "solitary"),
    "Hope": ("hope", "hopeful", "optimism", "light ahead"),
    "Fear": ("fear", "afraid", "terror", "anxious", "dread"),
    "Romance": ("romance", "romantic", "love", "intimate"),
    "Action": ("action", "chase", "fight", "explosion", "combat"),
    "Suspense": ("suspense", "thriller", "tension", "uneasy"),
    "Victory": ("victory", "triumph", "win", "celebration"),
    "Calm": ("calm", "peaceful", "serene", "quiet"),
    "Joy": ("happy", "joy", "cheerful", "celebrate"),
    "Anger": ("angry", "rage", "furious"),
    "Melancholy": ("melancholy", "melancholic", "nostalgic", "bittersweet"),
}

MOOD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Emotional": ("emotional", "heartfelt", "moving", "sad", "lonely", "alone"),
    "Epic": ("epic", "grand", "cinematic scale", "imax"),
    "Dark": ("dark", "grim", "noir", "sinister"),
    "Uplifting": ("uplifting", "inspiring", "motivational"),
    "Mysterious": ("mysterious", "enigmatic", "unknown"),
    "Energetic": ("energetic", "hype", "fast paced", "high energy"),
    "Intimate": ("intimate", "close", "personal", "whisper"),
    "Luxury": ("luxury", "premium", "elegant", "opulent"),
}

CAMERA_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Slow Dolly": ("slow dolly", "dolly in", "dolly out", "dolly"),
    "Close Up": ("close up", "close-up", "closeup", "cu "),
    "Medium Shot": ("medium shot", "mid shot", "ms "),
    "Wide Shot": ("wide shot", "wide angle", "establishing", "wideshot"),
    "Tracking Shot": ("tracking", "follow cam", "follow shot"),
    "Handheld": ("handheld", "shaky cam", "documentary cam"),
    "Aerial / Drone": ("drone", "aerial", "bird's eye", "birds eye"),
    "Steadicam": ("steadicam", "gimbal"),
    "Slow Motion": ("slow motion", "slow-mo", "slo mo", "slowmo"),
    "Macro": ("macro", "extreme detail"),
    "Over the Shoulder": ("over the shoulder", "ots"),
    "POV": ("pov", "point of view", "first person"),
}

MOVEMENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Slow walking": ("slow walk", "walking slowly", "walking alone", "walks alone", "walking"),
    "Running": ("running", "sprinting", "dash"),
    "Static hold": ("standing still", "frozen", "static"),
    "Push in": ("push in", "push-in", "creep in"),
    "Pull out": ("pull out", "pull-out", "reveal pull"),
    "Orbit": ("orbit", "circle around", "360"),
    "Pan": ("pan left", "pan right", "panning"),
    "Tilt": ("tilt up", "tilt down"),
    "Crash zoom": ("crash zoom", "snap zoom"),
}

LENS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "85mm portrait": ("portrait", "close up", "close-up", "face", "intimate"),
    "35mm narrative": ("street", "walking", "city", "road"),
    "24mm wide": ("wide", "landscape", "establishing", "vast"),
    "50mm natural": ("natural", "documentary", "interview"),
    "Anamorphic": ("anamorphic", "flare", "widescreen cinema"),
    "Macro lens": ("macro", "product detail", "texture"),
}

LIGHTING_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Low Key": ("low key", "low-key", "dark", "night", "shadow"),
    "High Key": ("high key", "high-key", "bright studio"),
    "Blue": ("blue light", "cold", "rain", "night", "moon"),
    "Golden": ("golden hour", "warm light", "sunset"),
    "Neon": ("neon", "cyber", "nightlife"),
    "Soft diffused": ("soft light", "diffused", "overcast"),
    "Hard contrast": ("hard light", "harsh", "noir"),
    "Rim light": ("rim light", "backlit", "silhouette"),
    "Wet reflections": ("rain", "wet", "puddle", "reflection"),
    "Practical lamps": ("lamp", "streetlight", "practical light"),
}

COLOR_PALETTE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Cold Blue": ("cold", "blue", "rain", "night", "lonely", "sad"),
    "Warm Amber": ("golden", "sunset", "warm", "amber", "cozy"),
    "Neon Magenta": ("neon", "cyber", "nightclub", "music video"),
    "Desaturated Grey": ("documentary", "overcast", "gritty", "noir"),
    "Pastel Soft": ("pastel", "anime", "soft", "dreamy"),
    "High Contrast Teal-Orange": ("trailer", "action", "blockbuster"),
    "Earth Natural": ("documentary", "outdoor", "nature"),
    "Luxury Black-Gold": ("luxury", "premium", "product", "watch"),
}

MUSIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Piano": ("sad", "lonely", "emotional", "melancholy", "alone", "piano"),
    "Ambient": ("rain", "night", "atmosphere", "ambient", "soft"),
    "Orchestral": ("epic", "trailer", "movie", "cinematic"),
    "Electronic Beat": ("tiktok", "reel", "shorts", "hype", "edm"),
    "Hip-Hop": ("rap", "hip hop", "hip-hop", "trap"),
    "Nasheed / Spiritual": ("islamic", "nasheed", "spiritual", "mosque"),
    "Corporate Clean": ("advertisement", "product", "corporate", "brand"),
    "Lo-fi": ("podcast", "chill", "lofi", "lo-fi"),
}

ENVIRONMENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Empty road": ("road", "street", "highway", "alone", "walking"),
    "City street": ("city", "urban", "downtown", "crosswalk"),
    "Interior room": ("room", "apartment", "bedroom", "office"),
    "Studio set": ("studio", "backdrop", "seamless", "podcast"),
    "Mosque / sacred space": ("mosque", "prayer", "minaret"),
    "Nature landscape": ("forest", "mountain", "field", "beach", "desert"),
    "Product tabletop": ("product", "tabletop", "packshot"),
    "Stage / performance": ("stage", "concert", "performance", "crowd"),
}

TRANSITION_BY_CATEGORY: dict[str, str] = {
    "Music Video": "beat-matched hard cuts + whip pans",
    "Advertisement": "clean dissolves + product punch-ins",
    "Movie Scene": "motivated cuts + emotional holds",
    "Documentary": "observational cuts + L-cuts",
    "Islamic Video": "gentle dissolves + respectful pacing",
    "Podcast": "speaker switches + subtle zooms",
    "Product Video": "macro inserts + seamless morphs",
    "Anime": "impact frames + speed lines",
    "3D Animation": "smooth camera blends + depth racks",
    "Talking Avatar": "hold + soft push for emphasis",
    "Short Film": "narrative match cuts",
    "Trailer": "smash cuts + title cards",
    "YouTube Shorts": "fast jump cuts + text pops",
    "TikTok": "hook cut within 1s + vertical smash cuts",
    "Instagram Reel": "trend-paced jump cuts + overlays",
}

# Map understanding category → legacy PromptIntelligenceResult fields
CATEGORY_TO_LEGACY: dict[str, tuple[str, str]] = {
    # (category, cinematic_genre)
    "Music Video": ("song", "music_video"),
    "Advertisement": ("business", "commercial"),
    "Movie Scene": ("story", "narrative"),
    "Documentary": ("story", "documentary"),
    "Islamic Video": ("religious", "narrative"),
    "Podcast": ("podcast", "documentary"),
    "Product Video": ("business", "commercial"),
    "Anime": ("cartoon", "narrative"),
    "3D Animation": ("cartoon", "narrative"),
    "Talking Avatar": ("business", "corporate"),
    "Short Film": ("story", "narrative"),
    "Trailer": ("story", "commercial"),
    "YouTube Shorts": ("business", "commercial"),
    "TikTok": ("song", "music_video"),
    "Instagram Reel": ("business", "commercial"),
}
