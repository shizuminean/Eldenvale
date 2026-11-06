[app]
title = Eldenvale RPG
package.name = eldenvale
package.domain = org.eldenvale
source.dir = .
source.include_exts = py,png,ttf
source.include_patterns = assets/*
source.exclude_dirs = .github,bin,.buildozer,__pycache__
version = 1.1
requirements = python3,pygame
orientation = landscape
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png
android.presplash_color = #0B1020
android.wakelock = True
fullscreen = 1
android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
p4a.bootstrap = sdl2
p4a.branch = v2023.09.16

[buildozer]
log_level = 2
warn_on_root = 1
