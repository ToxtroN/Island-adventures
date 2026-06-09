[app]
title = Island Adventures
package.name = islandadventures
package.domain = org.toxtron

source.dir = .
source.include_exts = py,png,jpg,mp3,mp4,json,ico,atlas
source.include_patterns = assets/*

version = 1.0

requirements = python3,kivy==2.3.0,pillow,android

orientation = landscape

# Иконка и заставка
icon.filename = assets/icon.png
presplash.filename = assets/splash.png
presplash.color = #1a0e00

# Android настройки
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True
android.release_artifact = apk

# Полноэкранный режим
android.fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1
