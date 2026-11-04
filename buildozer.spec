[app]
title = Eldenvale RPG
package.name = eldenvale
package.domain = org.eldenvale
source.dir = .
source.include_exts = py,png
source.include_patterns = assets/*
source.exclude_dirs = .github,bin,.buildozer,__pycache__
version = 1.0
requirements = python3,pygame
orientation = landscape
fullscreen = 1
android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
