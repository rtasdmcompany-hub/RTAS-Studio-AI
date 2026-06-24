# RTAS Mobile — Brand Asset Pipeline

Drop your premium master artwork here, then run asset generation from the monorepo root:

```bash
npm run mobile:assets
```

## Directory layout

```
assets/
├── icons/                    ← DROP ICON / LOGO MASTERS HERE
│   ├── logo-master.png       Easy mode (recommended): 1024×1024+ single logo
│   ├── logo-dark-master.png  Optional dark-mode logo variant
│   ├── icon-master.png       Full-control mode: 1024×1024+ app icon
│   └── README.md
├── splash/                   ← DROP SPLASH MASTERS HERE (full-control mode)
│   ├── splash-master.png     2732×2732+ cinematic splash artwork
│   ├── splash-dark-master.png Optional dark splash
│   └── README.md
├── logo.png                  (auto-staged — do not edit manually)
├── icon-only.png             (auto-staged — full-control mode)
└── splash.png                (auto-staged — full-control mode)
```

## Generation modes

| Mode | Drop files | Command output |
|------|------------|----------------|
| **Easy (recommended)** | `icons/logo-master.png` only | All iOS + Android icon densities + splash screens |
| **Full control** | `icons/icon-master.png` + `splash/splash-master.png` | Separate icon and splash crops |

## Brand defaults (RTAS cinematic)

Generation uses these colors automatically:

- Background: `#0a0a0f`
- Splash logo scale: `35%` of canvas

## After generation

Native projects are updated in place:

- **Android:** `android/app/src/main/res/mipmap-*`, `drawable*` splash layers
- **iOS:** `ios/App/App/Assets.xcassets/AppIcon.appiconset`, `Splash.imageset`

Then sync and open Android Studio:

```bash
npm run mobile:sync
npm run mobile:android
```
