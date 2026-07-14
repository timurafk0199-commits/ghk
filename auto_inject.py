#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IZIAPK Injector — автоматическая вставка приветственного диалога в APK.
Декомпиляция → инъекция smali + layout → сборка → подпись.
"""

import glob
import os
import re
import shutil
import subprocess
import sys
import threading
import xml.etree.ElementTree as ET
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# ═══════════════════════════════════════════════════════════════
#  НАСТРОЙКИ — измените под себя
# ═══════════════════════════════════════════════════════════════
TELEGRAM_URL = "https://t.me/ApkVzlomers"
BRAND_TITLE = "@ApkVzlomers"
FINAL_NAME_TEMPLATE = "{game_name} v{version} @ApkVzlomers.apk"
SCRIPT_DIR = Path(__file__).resolve().parent
LOGO_FILE = SCRIPT_DIR / "iziapk_logo.png"
DIRS = {
    "output": SCRIPT_DIR / "output",      # готовые APK
    "temp": SCRIPT_DIR / "temp",          # временные файлы (удаляются)
    "assets": SCRIPT_DIR / "assets",      # логотип, keystore
    "input": SCRIPT_DIR / "input",        # исходные APK (опционально)
}
OUTPUT_DIR = str(DIRS["temp"] / "game_src")
DIALOG_DELAY_MS = 2000

ANDROID_NS = "http://schemas.android.com/apk/res/android"

DIALOG_MESSAGE = (
    "Откройте для себя мир лучших модов и премиальных приложений! "
    "Подпишитесь на наш Telegram-канал — ваш надёжный источник топовых модов "
    "для игр, платных приложений и многого другого для Android, PC и iOS."
)
APKTOOL_TIMEOUT = 3600  # 1 час для больших APK

# ═══════════════════════════════════════════════════════════════
#  SMALI — AlertDialog без кастомных ресурсов (максимальная совместимость)
# ═══════════════════════════════════════════════════════════════
IZI_DIALOG_SMALI = r""".class public L%PKG%/IziDialog;
.super Ljava/lang/Object;
.source "IziDialog.java"


# static fields
.field private static sShown:Z


# direct methods
.method public constructor <init>()V
    .registers 1

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static show(Landroid/content/Context;)V
    .registers 6

    sget-boolean v0, L%PKG%/IziDialog;->sShown:Z

    if-nez v0, :already_shown

    const/4 v0, 0x1

    sput-boolean v0, L%PKG%/IziDialog;->sShown:Z

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v0

    new-instance v1, Landroid/os/Handler;

    invoke-direct {v1, v0}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    new-instance v2, L%PKG%/IziDialog$ShowRunnable;

    invoke-direct {v2, p0}, L%PKG%/IziDialog$ShowRunnable;-><init>(Landroid/content/Context;)V

    const-wide/16 v3, %DELAY%

    invoke-virtual {v1, v2, v3, v4}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    :already_shown
    return-void
.end method
"""

SHOW_RUNNABLE_SMALI = r""".class L%PKG%/IziDialog$ShowRunnable;
.class L%PKG%/IziDialog$ShowRunnable;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.source "IziDialog.java"


# instance fields
.field final synthetic val$ctx:Landroid/content/Context;


# direct methods
.method constructor <init>(Landroid/content/Context;)V
    .registers 2

    iput-object p1, p0, L%PKG%/IziDialog$ShowRunnable;->val$ctx:Landroid/content/Context;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 20

    iget-object v0, p0, L%PKG%/IziDialog$ShowRunnable;->val$ctx:Landroid/content/Context;

    instance-of v1, v0, Landroid/app/Activity;

    if-eqz v1, :end

    check-cast v0, Landroid/app/Activity;

    invoke-virtual {v0}, Landroid/app/Activity;->isFinishing()Z

    move-result v1

    if-nez v1, :end

    new-instance v1, Landroid/app/AlertDialog$Builder;

    invoke-direct {v1, v0}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V

    const/4 v2, 0x0

    invoke-virtual {v1, v2}, Landroid/app/AlertDialog$Builder;->setCancelable(Z)Landroid/app/AlertDialog$Builder;

    new-instance v3, Landroid/widget/LinearLayout;

    invoke-direct {v3, v0}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    const/4 v4, 0x1

    invoke-virtual {v3, v4}, Landroid/widget/LinearLayout;->setOrientation(I)V

    new-instance v5, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v6, -0x1

    const/4 v7, -0x2

    invoke-direct {v5, v6, v7}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    invoke-virtual {v3, v5}, Landroid/widget/LinearLayout;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    new-instance v8, Landroid/widget/LinearLayout;

    invoke-direct {v8, v0}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    invoke-virtual {v8, v4}, Landroid/widget/LinearLayout;->setOrientation(I)V

    const v9, 0xFF121212

    invoke-virtual {v8, v9}, Landroid/widget/LinearLayout;->setBackgroundColor(I)V

    new-instance v10, Landroid/widget/LinearLayout$LayoutParams;

    invoke-direct {v10, v6, v7}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    const/16 v11, 0x18

    iput v11, v10, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    iput v11, v10, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    iput v11, v10, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    iput v11, v10, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    invoke-virtual {v8, v10}, Landroid/widget/LinearLayout;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    const/16 v10, 0x11

    invoke-virtual {v8, v10}, Landroid/widget/LinearLayout;->setGravity(I)V

    new-instance v11, Landroid/widget/ImageView;

    invoke-direct {v11, v0}, Landroid/widget/ImageView;-><init>(Landroid/content/Context;)V

    const/16 v12, 0x50

    new-instance v13, Landroid/widget/LinearLayout$LayoutParams;

    invoke-direct {v13, v12, v12}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    const/16 v14, 0x10

    iput v14, v13, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    invoke-virtual {v11, v13}, Landroid/widget/ImageView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    invoke-virtual {v8, v11}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    new-instance v12, Landroid/widget/TextView;

    invoke-direct {v12, v0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    const-string v13, "@ApkVzlomers"

    invoke-virtual {v12, v13}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    const/high16 v13, 0x41a00000

    invoke-virtual {v12, v13}, Landroid/widget/TextView;->setTextSize(F)V

    const v13, 0xFFFFFFFF

    invoke-virtual {v12, v13}, Landroid/widget/TextView;->setTextColor(I)V

    invoke-virtual {v8, v12}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    invoke-virtual {v3, v8}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    new-instance v8, Landroid/widget/LinearLayout;

    invoke-direct {v8, v0}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    invoke-virtual {v8, v4}, Landroid/widget/LinearLayout;->setOrientation(I)V

    const v9, 0xFFFFFFFF

    invoke-virtual {v8, v9}, Landroid/widget/LinearLayout;->setBackgroundColor(I)V

    new-instance v10, Landroid/widget/LinearLayout$LayoutParams;

    invoke-direct {v10, v6, v7}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    invoke-virtual {v8, v10}, Landroid/widget/LinearLayout;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    new-instance v10, Landroid/widget/TextView;

    invoke-direct {v10, v0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    const-string v11, "%MESSAGE%"

    invoke-virtual {v10, v11}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    const v11, 0xFF666666

    invoke-virtual {v10, v11}, Landroid/widget/TextView;->setTextColor(I)V

    const/high16 v11, 0x41600000

    invoke-virtual {v10, v11}, Landroid/widget/TextView;->setTextSize(F)V

    new-instance v11, Landroid/widget/LinearLayout$LayoutParams;

    invoke-direct {v11, v6, v7}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    const/16 v12, 0x18

    iput v12, v11, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    iput v12, v11, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    iput v12, v11, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    const/16 v12, 0x10

    iput v12, v11, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    invoke-virtual {v10, v11}, Landroid/widget/TextView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    invoke-virtual {v8, v10}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    new-instance v10, Landroid/widget/Button;

    invoke-direct {v10, v0}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    const-string v11, "ПОДПИСАТЬСЯ"

    invoke-virtual {v10, v11}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    const v11, 0xFF1F77F5

    invoke-virtual {v10, v11}, Landroid/widget/Button;->setBackgroundColor(I)V

    const v11, 0xFFFFFFFF

    invoke-virtual {v10, v11}, Landroid/widget/Button;->setTextColor(I)V

    new-instance v11, Landroid/widget/LinearLayout$LayoutParams;

    invoke-direct {v11, v6, v7}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    const/16 v12, 0x18

    iput v12, v11, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    iput v12, v11, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    const/16 v12, 0x8

    iput v12, v11, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    invoke-virtual {v10, v11}, Landroid/widget/Button;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    new-instance v11, L%PKG%/IziDialog$ClickListener;

    invoke-direct {v11, v0}, L%PKG%/IziDialog$ClickListener;-><init>(Landroid/content/Context;)V

    invoke-virtual {v10, v11}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    invoke-virtual {v8, v10}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    invoke-virtual {v3, v8}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    invoke-virtual {v1, v3}, Landroid/app/AlertDialog$Builder;->setView(Landroid/view/View;)Landroid/app/AlertDialog$Builder;

    invoke-virtual {v1}, Landroid/app/AlertDialog$Builder;->create()Landroid/app/AlertDialog;

    move-result-object v1

    invoke-virtual {v1, v2}, Landroid/app/AlertDialog;->setCanceledOnTouchOutside(Z)V

    invoke-virtual {v1}, Landroid/app/AlertDialog;->show()V

    :end
    return-void
.end method
"""

CLICK_LISTENER_SMALI = r""".class L%PKG%/IziDialog$ClickListener;
.super Ljava/lang/Object;
.implements Landroid/content/DialogInterface$OnClickListener;
.source "IziDialog.java"


# instance fields
.field final synthetic val$ctx:Landroid/content/Context;


# direct methods
.method constructor <init>(Landroid/content/Context;)V
    .registers 2

    iput-object p1, p0, L%PKG%/IziDialog$ClickListener;->val$ctx:Landroid/content/Context;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public onClick(Landroid/content/DialogInterface;I)V
    .registers 5

    new-instance v0, Landroid/content/Intent;

    const-string v1, "android.intent.action.VIEW"

    const-string v2, "%TELEGRAM%"

    invoke-static {v2}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v2

    invoke-direct {v0, v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;Landroid/net/Uri;)V

    const/high16 v1, 0x10000000

    invoke-virtual {v0, v1}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;

    iget-object v1, p0, L%PKG%/IziDialog$ClickListener;->val$ctx:Landroid/content/Context;

    invoke-virtual {v1, v0}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V

    invoke-interface {p1}, Landroid/content/DialogInterface;->dismiss()V

    return-void
.end method
"""


# ═══════════════════════════════════════════════════════════════
#  УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════
def log_msg(log, msg):
    if log:
        log(msg)


def run_cmd(cmd, log=None, cwd=None, timeout=APKTOOL_TIMEOUT):
    log_msg(log, f"[CMD] {cmd}")
    proc = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    try:
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                log_msg(log, f"      {line}")
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise RuntimeError(f"Таймаут ({timeout}с). APK слишком большой или apktool завис.")
    if proc.returncode != 0:
        raise RuntimeError(f"Команда завершилась с кодом {proc.returncode}")
    return proc


def find_tool(name):
    path = shutil.which(name)
    if path:
        return path
    if sys.platform == "win32":
        path = shutil.which(name + ".bat") or shutil.which(name + ".exe")
        if path:
            return path
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if sdk:
        bt = Path(sdk) / "build-tools"
        if bt.is_dir():
            for ver in sorted(bt.iterdir(), reverse=True):
                for suffix in ("", ".bat", ".exe"):
                    cand = ver / f"{name}{suffix}"
                    if cand.exists():
                        return str(cand)
    return None


def ensure_apktool(log):
    if not shutil.which("apktool"):
        raise RuntimeError(
            "apktool не найден в PATH. Установите: choco install apktool"
        )
    log_msg(log, "[+] apktool найден")


def ensure_dirs(log=None):
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)
    for src in (SCRIPT_DIR / "iziapk_logo.png", SCRIPT_DIR / "apkvzlomers_logo.png"):
        if src.is_file():
            dst = DIRS["assets"] / src.name
            if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                shutil.copy2(src, dst)
    log_msg(log, "[+] Папки: output/, temp/, assets/, input/")


def cleanup_temp(log=None):
    temp = DIRS["temp"]
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    temp.mkdir(parents=True, exist_ok=True)
    for stray in (
        SCRIPT_DIR / "game_src", SCRIPT_DIR / "tmp_build.apk",
        SCRIPT_DIR / "tmp_ids", SCRIPT_DIR / "game_modified.apk",
    ):
        if stray.is_dir():
            shutil.rmtree(stray, ignore_errors=True)
        elif stray.is_file():
            stray.unlink(missing_ok=True)
    for pattern in ("*.idsig", "*.aligned"):
        for f in SCRIPT_DIR.glob(pattern):
            f.unlink(missing_ok=True)
    log_msg(log, "[+] Временные файлы удалены")


def decompile(apk, log):
    size_mb = os.path.getsize(apk) / (1024 * 1024)
    if size_mb > 100:
        log_msg(log, f"[!] Большой APK ({size_mb:.0f} MB) — декомпиляция может занять 10-30 минут")
        log_msg(log, "    Следите за логом ниже, это не зависание!")
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    run_cmd(f'apktool d "{apk}" -o "{OUTPUT_DIR}" -f', log)


def get_manifest_info(log):
    mf = os.path.join(OUTPUT_DIR, "AndroidManifest.xml")
    if not os.path.exists(mf):
        return None, None, None

    with open(mf, "r", encoding="utf-8") as f:
        txt = f.read()

    pkg = re.search(r'package\s*=\s*"([^"]+)"', txt)
    ver = re.search(r'android:versionName\s*=\s*"([^"]+)"', txt)
    package = pkg.group(1) if pkg else None
    version = ver.group(1) if ver else "1.0"

    # Попытка через ElementTree для launcher activity
    launcher = None
    try:
        root = ET.fromstring(txt)
        for activity in root.iter("activity"):
            name = activity.get(f"{{{ANDROID_NS}}}name")
            if not name:
                continue
            for filt in activity.findall("intent-filter"):
                actions = {
                    a.get(f"{{{ANDROID_NS}}}name")
                    for a in filt.findall("action")
                }
                categories = {
                    c.get(f"{{{ANDROID_NS}}}name")
                    for c in filt.findall("category")
                }
                if (
                    "android.intent.action.MAIN" in actions
                    and "android.intent.category.LAUNCHER" in categories
                ):
                    launcher = name
                    break
            if launcher:
                break
    except ET.ParseError:
        pass

    if not launcher:
        pat = (
            r'<activity[^>]*android:name\s*=\s*"([^"]+)"[^>]*>'
            r'.*?android\.intent\.category\.LAUNCHER'
        )
        m = re.search(pat, txt, re.DOTALL)
        if m:
            launcher = m.group(1)

    if launcher and launcher.startswith("."):
        launcher = package + launcher if package else launcher[1:]
    elif launcher and "." not in launcher and package:
        launcher = f"{package}.{launcher}"

    log_msg(log, f"[*] Пакет: {package}")
    log_msg(log, f"[*] Версия: {version}")
    log_msg(log, f"[*] Launcher: {launcher or 'не найден'}")

    return package, version, launcher


def resolve_smali_path(class_name):
    rel = class_name.replace(".", os.sep) + ".smali"
    basename = os.path.basename(rel)

    candidates = []
    for smali_root in sorted(glob.glob(os.path.join(OUTPUT_DIR, "smali*"))):
        full = os.path.join(smali_root, rel)
        if os.path.isfile(full):
            candidates.append(full)

    if candidates:
        return candidates[0]

    for smali_root in sorted(glob.glob(os.path.join(OUTPUT_DIR, "smali*"))):
        for root, _, files in os.walk(smali_root):
            if basename in files:
                return os.path.join(root, basename)

    return None


def find_launcher_smali(launcher_class, log):
    if launcher_class:
        path = resolve_smali_path(launcher_class)
        if path:
            return path

    for smali_root in sorted(glob.glob(os.path.join(OUTPUT_DIR, "smali*"))):
        for root, _, files in os.walk(smali_root):
            for fname in files:
                if fname.endswith(".smali") and (
                    fname == "MainActivity.smali"
                    or fname == "UnityPlayerActivity.smali"
                    or fname == "GameActivity.smali"
                ):
                    found = os.path.join(root, fname)
                    log_msg(log, f"[!] Fallback activity: {found}")
                    return found

    return None


def pick_smali_dir(package_slash, log):
    rel = package_slash.replace("/", os.sep)
    for smali_root in sorted(glob.glob(os.path.join(OUTPUT_DIR, "smali*"))):
        target = os.path.join(smali_root, rel)
        if os.path.isdir(target):
            return target
    first = sorted(glob.glob(os.path.join(OUTPUT_DIR, "smali*")))
    if not first:
        raise RuntimeError("Папки smali не найдены после декомпиляции")
    target = os.path.join(first[0], rel)
    os.makedirs(target, exist_ok=True)
    log_msg(log, f"[+] Smali для инъекции: {target}")
    return target


def write_smali_files(package_slash, telegram_url, log):
    smali_dir = pick_smali_dir(package_slash, log)
    delay_hex = f"0x{DIALOG_DELAY_MS:x}"
    msg = DIALOG_MESSAGE.replace('"', '\\"')
    files = {
        "IziDialog.smali": IZI_DIALOG_SMALI,
        "IziDialog$ShowRunnable.smali": SHOW_RUNNABLE_SMALI,
        "IziDialog$ClickListener.smali": CLICK_LISTENER_SMALI,
    }
    for fname, tmpl in files.items():
        content = (
            tmpl.replace("%PKG%", package_slash)
            .replace("%TELEGRAM%", telegram_url)
            .replace("%MESSAGE%", msg)
            .replace("%DELAY%", delay_hex)
        )
        path = os.path.join(smali_dir, fname)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        log_msg(log, f"[+] {path}")


def find_method_range(lines, signatures):
    for sig in signatures:
        for i, line in enumerate(lines):
            if sig in line:
                end = i + 1
                while end < len(lines) and ".end method" not in lines[end]:
                    end += 1
                return i, end, sig
    return None, None, None


def inject_new_onresume(activity_path, package_slash, lines, log):
    marker = "INJECT_IZIAPK_DIALOG"
    full_text = "".join(lines)
    if marker in full_text:
        log_msg(log, "[!] Инъекция уже присутствует — пропуск")
        return True

    super_class = "Landroid/app/Activity;"
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(".super "):
            super_class = stripped.split(" ", 1)[1].strip()
            break

    new_method = (
        f"\n.method public onResume()V\n"
        f"    .locals 0\n"
        f"\n"
        f"    # === {marker} ===\n"
        f"    invoke-super {{p0}}, {super_class}->onResume()V\n"
        f"    invoke-static {{p0}}, L{package_slash}/IziDialog;"
        f"->show(Landroid/content/Context;)V\n"
        f"    # === END {marker} ===\n"
        f"\n"
        f"    return-void\n"
        f".end method\n"
    )

    lines.append(new_method)

    with open(activity_path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)

    log_msg(log, f"[+] Добавлен новый onResume() в: {activity_path}")
    log_msg(log, f"    Родительский класс (super): {super_class}")
    return True


def patch_launcher_activity(activity_path, package_slash, log):
    if not activity_path or not os.path.isfile(activity_path):
        log_msg(log, "[!] Launcher activity не найдена")
        return False

    with open(activity_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    signatures = [
        ".method public onWindowFocusChanged(Z)V",
        ".method protected onWindowFocusChanged(Z)V",
        ".method public final onWindowFocusChanged(Z)V",
        ".method protected onWindowFocusChanged(Z)V",
        ".method protected onResume()V",
        ".method public onResume()V",
        ".method public final onResume()V",
        ".method protected final onResume()V",
    ]

    start, end, sig = find_method_range(lines, signatures)
    if start is None:
        log_msg(log, "[!] onWindowFocusChanged/onResume не найден в activity — создаю новый onResume()")
        return inject_new_onresume(activity_path, package_slash, lines, log)

    marker = "INJECT_IZIAPK_DIALOG"
    use_focus_guard = "onWindowFocusChanged" in sig
    if use_focus_guard:
        inject_block = (
            f"    # === {marker} ===\n"
            f"    if-eqz p1, :cond_izi_skip\n"
            f"    invoke-static {{p0}}, L{package_slash}/IziDialog;"
            f"->show(Landroid/content/Context;)V\n"
            f"    :cond_izi_skip\n"
            f"    # === END {marker} ===\n"
        )
    else:
        inject_block = (
            f"    # === {marker} ===\n"
            f"    invoke-static {{p0}}, L{package_slash}/IziDialog;"
            f"->show(Landroid/content/Context;)V\n"
            f"    # === END {marker} ===\n"
        )

    method_body = "".join(lines[start:end])
    if marker in method_body:
        log_msg(log, "[!] Инъекция уже присутствует — пропуск")
        return True

    insert_at = None
    for i in range(start, end):
        if "invoke-super" in lines[i]:
            insert_at = i + 1
            break

    if insert_at is None:
        for i in range(start + 1, end):
            stripped = lines[i].strip()
            if stripped and not stripped.startswith("."):
                insert_at = i
                break

    if insert_at is None:
        log_msg(log, "[!] Не удалось найти место вставки")
        return False

    lines.insert(insert_at, inject_block)

    with open(activity_path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)

    log_msg(log, f"[+] Пропатчено: {activity_path}")
    log_msg(log, f"    Метод: {sig.strip()}")
    return True


def build_apk(output_name, log):
    run_cmd(f'apktool b "{OUTPUT_DIR}" -o "{output_name}"', log)


KEYSTORE_TYPE = "JKS"
KEYSTORE_PASS = "android"
KEY_ALIAS = "iziapk"


def ensure_keystore(log):
    keystore = DIRS["assets"] / "iziapk.keystore"
    legacy = SCRIPT_DIR / "iziapk.keystore"
    if not keystore.is_file() and legacy.is_file():
        shutil.move(str(legacy), str(keystore))
    if keystore.is_file():
        try:
            run_cmd(
                f'keytool -list -keystore "{keystore}" -storepass {KEYSTORE_PASS} '
                f"-storetype {KEYSTORE_TYPE}",
                log,
            )
            return keystore
        except RuntimeError:
            log_msg(log, "[!] Keystore повреждён — пересоздаю...")
            keystore.unlink(missing_ok=True)

    run_cmd(
        f'keytool -genkey -v -keystore "{keystore}" -alias {KEY_ALIAS} '
        f"-keyalg RSA -keysize 2048 -validity 10000 "
        f"-storetype {KEYSTORE_TYPE} "
        f"-storepass {KEYSTORE_PASS} -keypass {KEYSTORE_PASS} "
        f'-dname "CN=IZIAPK, OU=IZIAPK, O=IZIAPK, L=City, ST=State, C=RU"',
        log,
    )
    log_msg(log, f"[+] Keystore создан ({KEYSTORE_TYPE})")
    return keystore


def sign_apk(apk_path, log):
    keystore = ensure_keystore(log)

    apksigner = find_tool("apksigner")
    if apksigner:
        cmd = (
            f'"{apksigner}" sign --ks "{keystore}" '
            f"--ks-pass pass:{KEYSTORE_PASS} --key-pass pass:{KEYSTORE_PASS} "
            f"--ks-key-alias {KEY_ALIAS} "
            f"--v1-signing-enabled true --v2-signing-enabled true "
            f'"{apk_path}"'
        )
        if KEYSTORE_TYPE != "JKS":
            cmd = cmd.replace(
                f'--ks-pass pass:{KEYSTORE_PASS}',
                f"--ks-type {KEYSTORE_TYPE} --ks-pass pass:{KEYSTORE_PASS}",
            )
        run_cmd(cmd, log)
        log_msg(log, "[+] APK подписан (apksigner)")
        return True

    uber = SCRIPT_DIR / "uber-apk-signer.jar"
    if not uber.is_file():
        found = sorted(SCRIPT_DIR.glob("uber-apk-signer*.jar"))
        if found:
            uber = found[0]
    if uber.is_file():
        run_cmd(
            f'java -jar "{uber}" -a "{apk_path}" --overwrite '
            f"--allowResign",
            log,
        )
        log_msg(log, "[+] APK подписан (uber-apk-signer)")
        return True

    log_msg(log, "[!] Подписчик не найден — подпишите APK вручную")
    return False


def zipalign_apk(apk_path, log):
    zipalign = find_tool("zipalign")
    if not zipalign:
        log_msg(log, "[!] zipalign не найден — пропуск")
        return

    aligned = apk_path + ".aligned"
    run_cmd(f'"{zipalign}" -f -p 4 "{apk_path}" "{aligned}"', log)
    os.replace(aligned, apk_path)
    log_msg(log, "[+] APK выровнен (zipalign)")


def normalize_telegram_url(url):
    url = (url or "").strip()
    if url.startswith("@"):
        return f"https://t.me/{url[1:]}"
    if url.startswith("t.me/"):
        return f"https://{url}"
    return url


def process_apk(apk_input, telegram_url, log, progress=None, index=0, total=1):
    try:
        telegram_url = normalize_telegram_url(telegram_url)
        ensure_dirs()
        cleanup_temp()
        ensure_apktool(log)

        prefix = f"[{index}/{total}] " if total > 1 else ""
        if progress:
            progress(5, f"{prefix}Проверка файла...")
        if not os.path.isfile(apk_input):
            raise RuntimeError("APK-файл не существует")

        if progress:
            progress(10, f"{prefix}Декомпиляция...")
        decompile(apk_input, log)

        if progress:
            progress(25, f"{prefix}Манифест...")
        package, version, launcher = get_manifest_info(log)
        if not package:
            raise RuntimeError("Не удалось определить package из манифеста")

        package_slash = package.replace(".", "/")

        if progress:
            progress(35, f"{prefix}Добавление smali...")
        write_smali_files(package_slash, telegram_url, log)

        if progress:
            progress(50, f"{prefix}Патч activity...")
        activity = find_launcher_smali(launcher, log)
        if not patch_launcher_activity(activity, package_slash, log):
            raise RuntimeError("Не удалось внедрить вызов диалога")

        if progress:
            progress(70, f"{prefix}Сборка APK...")
        final_apk = str(DIRS["temp"] / "game_modified.apk")
        build_apk(final_apk, log)

        if progress:
            progress(85, f"{prefix}Выравнивание и подпись...")
        zipalign_apk(final_apk, log)
        sign_apk(final_apk, log)

        base_name = os.path.splitext(os.path.basename(apk_input))[0]
        out_name = FINAL_NAME_TEMPLATE.format(game_name=base_name, version=version)
        out_path = DIRS["output"] / out_name
        if out_path.is_file():
            out_path.unlink()
        shutil.move(final_apk, str(out_path))

        cleanup_temp(log)

        if progress:
            progress(100, f"{prefix}Готово!")
        log_msg(log, f"[+] Успех! → {out_path}")
        return str(out_path)

    except Exception as exc:
        log_msg(log, f"[!] ОШИБКА ({os.path.basename(apk_input)}): {exc}")
        cleanup_temp(log)
        return None


def process_multiple(apk_list, telegram_url, log, progress=None):
    results = []
    total = len(apk_list)
    for i, apk in enumerate(apk_list, 1):
        log_msg(log, f"\n{'='*50}")
        log_msg(log, f"[*] Обработка {i}/{total}: {os.path.basename(apk)}")
        log_msg(log, f"{'='*50}")
        result = process_apk(apk, telegram_url, log, progress, i, total)
        results.append((apk, result))
    return results


# ═══════════════════════════════════════════════════════════════
#  GUI
# ═══════════════════════════════════════════════════════════════
class InjectorApp:
    COLORS = {
        "bg": "#0f1419",
        "panel": "#1a2332",
        "accent": "#1E88E5",
        "accent2": "#00BCD4",
        "text": "#e8edf3",
        "muted": "#8b9cb3",
        "input_bg": "#243044",
    }

    def __init__(self, root):
        self.root = root
        self.running = False
        root.title("IZIAPK Injector")
        root.geometry("760x640")
        root.resizable(False, False)
        root.configure(bg=self.COLORS["bg"])

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.TFrame", background=self.COLORS["bg"]
        )
        style.configure(
            "Panel.TFrame", background=self.COLORS["panel"]
        )
        style.configure(
            "Title.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["accent2"],
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Sub.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Panel.TLabel",
            background=self.COLORS["panel"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=(16, 8),
        )
        style.configure(
            "TProgressbar",
            troughcolor=self.COLORS["input_bg"],
            background=self.COLORS["accent2"],
            thickness=8,
        )

        main = ttk.Frame(root, style="Dark.TFrame", padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main,
            text="IZIAPK INJECTOR",
            style="Title.TLabel",
        ).pack(anchor=tk.W)
        ttk.Label(
            main,
            text="Автоматическая вставка диалога подписки в APK",
            style="Sub.TLabel",
        ).pack(anchor=tk.W, pady=(0, 16))

        panel = ttk.Frame(main, style="Panel.TFrame", padding=16)
        panel.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(
            panel, text="APK-файлы (можно несколько):", style="Panel.TLabel"
        ).pack(anchor=tk.W)

        list_row = ttk.Frame(panel, style="Panel.TFrame")
        list_row.pack(fill=tk.X, pady=(6, 8))

        self.apk_listbox = tk.Listbox(
            list_row,
            height=4,
            font=("Segoe UI", 9),
            bg=self.COLORS["input_bg"],
            fg=self.COLORS["text"],
            selectbackground=self.COLORS["accent"],
            relief=tk.FLAT,
            bd=6,
        )
        self.apk_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        btn_col = ttk.Frame(list_row, style="Panel.TFrame")
        btn_col.pack(side=tk.RIGHT)

        for text, cmd, color in [
            ("+ Добавить", self.add_apks, self.COLORS["accent"]),
            ("- Убрать", self.remove_apk, "#455A64"),
            ("Очистить", self.clear_apks, "#455A64"),
        ]:
            tk.Button(
                btn_col, text=text, command=cmd,
                bg=color, fg="white", relief=tk.FLAT,
                padx=10, pady=4, cursor="hand2",
            ).pack(fill=tk.X, pady=2)

        ttk.Label(
            panel, text="Готовые APK → папка output/", style="Panel.TLabel",
        ).pack(anchor=tk.W, pady=(0, 4))

        ttk.Label(
            panel, text="Telegram-канал (URL):", style="Panel.TLabel"
        ).pack(anchor=tk.W)

        self.tg_var = tk.StringVar(value=TELEGRAM_URL)
        tg_entry = tk.Entry(
            panel,
            textvariable=self.tg_var,
            font=("Segoe UI", 10),
            bg=self.COLORS["input_bg"],
            fg=self.COLORS["text"],
            insertbackground=self.COLORS["text"],
            relief=tk.FLAT,
            bd=6,
        )
        tg_entry.pack(fill=tk.X, pady=(6, 0))

        self.progress = ttk.Progressbar(
            main, orient=tk.HORIZONTAL, mode="determinate", length=680
        )
        self.progress.pack(fill=tk.X, pady=(4, 10))

        self.status_var = tk.StringVar(value="Готов к работе")
        ttk.Label(
            main,
            textvariable=self.status_var,
            style="Sub.TLabel",
        ).pack(anchor=tk.W)

        self.start_btn = tk.Button(
            main,
            text="▶  ЗАПУСТИТЬ ИНЪЕКЦИЮ",
            command=self.start,
            bg=self.COLORS["accent2"],
            fg="#0f1419",
            activebackground="#26C6DA",
            activeforeground="#0f1419",
            relief=tk.FLAT,
            font=("Segoe UI", 12, "bold"),
            padx=20,
            pady=10,
            cursor="hand2",
        )
        self.start_btn.pack(pady=12)

        log_frame = ttk.Frame(main, style="Dark.TFrame")
        log_frame.pack(fill=tk.BOTH, expand=True)

        log_toolbar = ttk.Frame(log_frame, style="Dark.TFrame")
        log_toolbar.pack(fill=tk.X)

        copy_btn = tk.Button(
            log_toolbar,
            text="📋 Копировать лог",
            command=self.copy_log,
            bg="#2d333b",
            fg="#e6edf3",
            activebackground="#3d444d",
            activeforeground="#e6edf3",
            relief=tk.FLAT,
            font=("Segoe UI", 9),
            padx=10,
            pady=4,
            cursor="hand2",
        )
        copy_btn.pack(anchor=tk.E, pady=(0, 4))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            font=("Consolas", 9),
            bg="#0a0e14",
            fg="#7ee787",
            insertbackground="#7ee787",
            relief=tk.FLAT,
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def copy_log(self):
        content = self.log_text.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_var.set("Лог скопирован в буфер обмена")

    def add_apks(self):
        paths = filedialog.askopenfilenames(
            title="Выберите APK (можно несколько)",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")],
        )
        existing = set(self.apk_listbox.get(0, tk.END))
        for p in paths:
            if p and p not in existing:
                self.apk_listbox.insert(tk.END, p)

    def remove_apk(self):
        sel = self.apk_listbox.curselection()
        for i in reversed(sel):
            self.apk_listbox.delete(i)

    def clear_apks(self):
        self.apk_listbox.delete(0, tk.END)

    def get_apk_list(self):
        return list(self.apk_listbox.get(0, tk.END))

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def set_progress(self, val, text=""):
        self.progress["value"] = val
        if text:
            self.status_var.set(text)
        self.root.update_idletasks()

    def start(self):
        if self.running:
            return

        apks = self.get_apk_list()
        telegram = normalize_telegram_url(self.tg_var.get().strip())

        if not apks:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один APK-файл.")
            return
        missing = [a for a in apks if not os.path.isfile(a)]
        if missing:
            messagebox.showerror(
                "Ошибка",
                "Некоторые файлы не найдены:\n" + "\n".join(missing),
            )
            return
        if "t.me/" not in telegram:
            messagebox.showwarning(
                "Внимание",
                "Укажите ссылку на Telegram-канал.\n"
                "Примеры: https://t.me/iziapk  или  @iziapk",
            )
            return

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.log_text.delete("1.0", tk.END)
        self.progress["value"] = 0
        self.log(f"[INFO] Старт обработки {len(apks)} APK...")
        self.log(f"[INFO] auto_inject.py build: FIX-6 (двухцветный layout: чёрный верх + белый низ)")
        ensure_dirs()
        threading.Thread(
            target=self._worker, args=(apks, telegram), daemon=True
        ).start()

    def _worker(self, apks, telegram):
        results = process_multiple(apks, telegram, self.log, self.set_progress)
        self.running = False
        self.start_btn.config(state=tk.NORMAL)

        ok = [r for _, r in results if r]
        fail = len(results) - len(ok)

        if ok and not fail:
            self.status_var.set("Готово!")
            messagebox.showinfo(
                "Успех",
                f"Обработано: {len(ok)} APK\n\n"
                f"Папка: {DIRS['output']}\n\n"
                "Диалог появится через 2 сек после загрузки игры.\n"
                "Закрыть можно только кнопкой «ПОДПИСАТЬСЯ».",
            )
        elif ok:
            self.status_var.set(f"Готово: {len(ok)}, ошибок: {fail}")
            messagebox.showwarning(
                "Частично",
                f"Успешно: {len(ok)}\nОшибок: {fail}\n\n"
                f"Смотрите лог. Готовые APK в {DIRS['output']}",
            )
        else:
            self.status_var.set("Ошибка")
            messagebox.showerror("Ошибка", "Ни один APK не обработан. Смотрите лог.")


def main():
    ensure_dirs()
    if len(sys.argv) >= 2:
        tg = sys.argv[-1] if sys.argv[-1].startswith(("http", "@", "t.me")) else TELEGRAM_URL
        apks = [a for a in sys.argv[1:] if a.endswith(".apk")]
        if not apks:
            print("[!] Укажите APK: python auto_inject.py file1.apk [file2.apk ...] [telegram_url]")
            sys.exit(1)
        results = process_multiple(apks, tg, print, None)
        sys.exit(0 if all(r for _, r in results) else 1)

    root = tk.Tk()
    InjectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

CLICK_LISTENER_SMALI = r""".class L%PKG%/IziDialog$ClickListener;
.super Ljava/lang/Object;
.implements Landroid/content/DialogInterface$OnClickListener;
.source "IziDialog.java"


# instance fields
.field final synthetic val$ctx:Landroid/content/Context;


# direct methods
.method constructor <init>(Landroid/content/Context;)V
    .registers 2

    iput-object p1, p0, L%PKG%/IziDialog$ClickListener;->val$ctx:Landroid/content/Context;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public onClick(Landroid/content/DialogInterface;I)V
    .registers 5

    new-instance v0, Landroid/content/Intent;

    const-string v1, "android.intent.action.VIEW"

    const-string v2, "%TELEGRAM%"

    invoke-static {v2}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v2

    invoke-direct {v0, v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;Landroid/net/Uri;)V

    const/high16 v1, 0x10000000

    invoke-virtual {v0, v1}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;

    iget-object v1, p0, L%PKG%/IziDialog$ClickListener;->val$ctx:Landroid/content/Context;

    invoke-virtual {v1, v0}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V

    invoke-interface {p1}, Landroid/content/DialogInterface;->dismiss()V

    return-void
.end method
"""


# ═══════════════════════════════════════════════════════════════
#  УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════
def log_msg(log, msg):
    if log:
        log(msg)


def run_cmd(cmd, log=None, cwd=None, timeout=APKTOOL_TIMEOUT):
    log_msg(log, f"[CMD] {cmd}")
    proc = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    try:
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                log_msg(log, f"      {line}")
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise RuntimeError(f"Таймаут ({timeout}с). APK слишком большой или apktool завис.")
    if proc.returncode != 0:
        raise RuntimeError(f"Команда завершилась с кодом {proc.returncode}")
    return proc


def find_tool(name):
    path = shutil.which(name)
    if path:
        return path
    if sys.platform == "win32":
        path = shutil.which(name + ".bat") or shutil.which(name + ".exe")
        if path:
            return path
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if sdk:
        bt = Path(sdk) / "build-tools"
        if bt.is_dir():
            for ver in sorted(bt.iterdir(), reverse=True):
                for suffix in ("", ".bat", ".exe"):
                    cand = ver / f"{name}{suffix}"
                    if cand.exists():
                        return str(cand)
    return None


def ensure_apktool(log):
    if not shutil.which("apktool"):
        raise RuntimeError(
            "apktool не найден в PATH. Установите: choco install apktool"
        )
    log_msg(log, "[+] apktool найден")


def ensure_dirs(log=None):
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)
    for src in (SCRIPT_DIR / "iziapk_logo.png", SCRIPT_DIR / "apkvzlomers_logo.png"):
        if src.is_file():
            dst = DIRS["assets"] / src.name
            if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                shutil.copy2(src, dst)
    log_msg(log, "[+] Папки: output/, temp/, assets/, input/")


def cleanup_temp(log=None):
    temp = DIRS["temp"]
    if temp.exists():
        shutil.rmtree(temp, ignore_errors=True)
    temp.mkdir(parents=True, exist_ok=True)
    for stray in (
        SCRIPT_DIR / "game_src", SCRIPT_DIR / "tmp_build.apk",
        SCRIPT_DIR / "tmp_ids", SCRIPT_DIR / "game_modified.apk",
    ):
        if stray.is_dir():
            shutil.rmtree(stray, ignore_errors=True)
        elif stray.is_file():
            stray.unlink(missing_ok=True)
    for pattern in ("*.idsig", "*.aligned"):
        for f in SCRIPT_DIR.glob(pattern):
            f.unlink(missing_ok=True)
    log_msg(log, "[+] Временные файлы удалены")


def decompile(apk, log):
    size_mb = os.path.getsize(apk) / (1024 * 1024)
    if size_mb > 100:
        log_msg(log, f"[!] Большой APK ({size_mb:.0f} MB) — декомпиляция может занять 10-30 минут")
        log_msg(log, "    Следите за логом ниже, это не зависание!")
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    run_cmd(f'apktool d "{apk}" -o "{OUTPUT_DIR}" -f', log)


def get_manifest_info(log):
    mf = os.path.join(OUTPUT_DIR, "AndroidManifest.xml")
    if not os.path.exists(mf):
        return None, None, None

    with open(mf, "r", encoding="utf-8") as f:
        txt = f.read()

    pkg = re.search(r'package\s*=\s*"([^"]+)"', txt)
    ver = re.search(r'android:versionName\s*=\s*"([^"]+)"', txt)
    package = pkg.group(1) if pkg else None
    version = ver.group(1) if ver else "1.0"

    # Попытка через ElementTree для launcher activity
    launcher = None
    try:
        root = ET.fromstring(txt)
        for activity in root.iter("activity"):
            name = activity.get(f"{{{ANDROID_NS}}}name")
            if not name:
                continue
            for filt in activity.findall("intent-filter"):
                actions = {
                    a.get(f"{{{ANDROID_NS}}}name")
                    for a in filt.findall("action")
                }
                categories = {
                    c.get(f"{{{ANDROID_NS}}}name")
                    for c in filt.findall("category")
                }
                if (
                    "android.intent.action.MAIN" in actions
                    and "android.intent.category.LAUNCHER" in categories
                ):
                    launcher = name
                    break
            if launcher:
                break
    except ET.ParseError:
        pass

    if not launcher:
        pat = (
            r'<activity[^>]*android:name\s*=\s*"([^"]+)"[^>]*>'
            r'.*?android\.intent\.category\.LAUNCHER'
        )
        m = re.search(pat, txt, re.DOTALL)
        if m:
            launcher = m.group(1)

    if launcher and launcher.startswith("."):
        launcher = package + launcher if package else launcher[1:]
    elif launcher and "." not in launcher and package:
        launcher = f"{package}.{launcher}"

    log_msg(log, f"[*] Пакет: {package}")
    log_msg(log, f"[*] Версия: {version}")
    log_msg(log, f"[*] Launcher: {launcher or 'не найден'}")

    return package, version, launcher


def resolve_smali_path(class_name):
    rel = class_name.replace(".", os.sep) + ".smali"
    basename = os.path.basename(rel)

    candidates = []
    for smali_root in sorted(glob.glob(os.path.join(OUTPUT_DIR, "smali*"))):
        full = os.path.join(smali_root, rel)
        if os.path.isfile(full):
            candidates.append(full)

    if candidates:
        return candidates[0]

    for smali_root in sorted(glob.glob(os.path.join(OUTPUT_DIR, "smali*"))):
        for root, _, files in os.walk(smali_root):
            if basename in files:
                return os.path.join(root, basename)

    return None


def find_launcher_smali(launcher_class, log):
    if launcher_class:
        path = resolve_smali_path(launcher_class)
        if path:
            return path

    for smali_root in sorted(glob.glob(os.path.join(OUTPUT_DIR, "smali*"))):
        for root, _, files in os.walk(smali_root):
            for fname in files:
                if fname.endswith(".smali") and (
                    fname == "MainActivity.smali"
                    or fname == "UnityPlayerActivity.smali"
                    or fname == "GameActivity.smali"
                ):
                    found = os.path.join(root, fname)
                    log_msg(log, f"[!] Fallback activity: {found}")
                    return found

    return None


def pick_smali_dir(package_slash, log):
    rel = package_slash.replace("/", os.sep)
    for smali_root in sorted(glob.glob(os.path.join(OUTPUT_DIR, "smali*"))):
        target = os.path.join(smali_root, rel)
        if os.path.isdir(target):
            return target
    first = sorted(glob.glob(os.path.join(OUTPUT_DIR, "smali*")))
    if not first:
        raise RuntimeError("Папки smali не найдены после декомпиляции")
    target = os.path.join(first[0], rel)
    os.makedirs(target, exist_ok=True)
    log_msg(log, f"[+] Smali для инъекции: {target}")
    return target


def write_smali_files(package_slash, telegram_url, log):
    smali_dir = pick_smali_dir(package_slash, log)
    delay_hex = f"0x{DIALOG_DELAY_MS:x}"
    msg = DIALOG_MESSAGE.replace('"', '\\"')
    files = {
        "IziDialog.smali": IZI_DIALOG_SMALI,
        "IziDialog$ShowRunnable.smali": SHOW_RUNNABLE_SMALI,
        "IziDialog$ClickListener.smali": CLICK_LISTENER_SMALI,
    }
    for fname, tmpl in files.items():
        content = (
            tmpl.replace("%PKG%", package_slash)
            .replace("%TELEGRAM%", telegram_url)
            .replace("%MESSAGE%", msg)
            .replace("%DELAY%", delay_hex)
        )
        path = os.path.join(smali_dir, fname)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        log_msg(log, f"[+] {path}")


def find_method_range(lines, signatures):
    for sig in signatures:
        for i, line in enumerate(lines):
            if sig in line:
                end = i + 1
                while end < len(lines) and ".end method" not in lines[end]:
                    end += 1
                return i, end, sig
    return None, None, None


def inject_new_onresume(activity_path, package_slash, lines, log):
    marker = "INJECT_IZIAPK_DIALOG"
    full_text = "".join(lines)
    if marker in full_text:
        log_msg(log, "[!] Инъекция уже присутствует — пропуск")
        return True

    super_class = "Landroid/app/Activity;"
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(".super "):
            super_class = stripped.split(" ", 1)[1].strip()
            break

    new_method = (
        f"\n.method public onResume()V\n"
        f"    .locals 0\n"
        f"\n"
        f"    # === {marker} ===\n"
        f"    invoke-super {{p0}}, {super_class}->onResume()V\n"
        f"    invoke-static {{p0}}, L{package_slash}/IziDialog;"
        f"->show(Landroid/content/Context;)V\n"
        f"    # === END {marker} ===\n"
        f"\n"
        f"    return-void\n"
        f".end method\n"
    )

    lines.append(new_method)

    with open(activity_path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)

    log_msg(log, f"[+] Добавлен новый onResume() в: {activity_path}")
    log_msg(log, f"    Родительский класс (super): {super_class}")
    return True


def patch_launcher_activity(activity_path, package_slash, log):
    if not activity_path or not os.path.isfile(activity_path):
        log_msg(log, "[!] Launcher activity не найдена")
        return False

    with open(activity_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    signatures = [
        ".method public onWindowFocusChanged(Z)V",
        ".method protected onWindowFocusChanged(Z)V",
        ".method public final onWindowFocusChanged(Z)V",
        ".method protected onWindowFocusChanged(Z)V",
        ".method protected onResume()V",
        ".method public onResume()V",
        ".method public final onResume()V",
        ".method protected final onResume()V",
    ]

    start, end, sig = find_method_range(lines, signatures)
    if start is None:
        log_msg(log, "[!] onWindowFocusChanged/onResume не найден в activity — создаю новый onResume()")
        return inject_new_onresume(activity_path, package_slash, lines, log)

    marker = "INJECT_IZIAPK_DIALOG"
    use_focus_guard = "onWindowFocusChanged" in sig
    if use_focus_guard:
        inject_block = (
            f"    # === {marker} ===\n"
            f"    if-eqz p1, :cond_izi_skip\n"
            f"    invoke-static {{p0}}, L{package_slash}/IziDialog;"
            f"->show(Landroid/content/Context;)V\n"
            f"    :cond_izi_skip\n"
            f"    # === END {marker} ===\n"
        )
    else:
        inject_block = (
            f"    # === {marker} ===\n"
            f"    invoke-static {{p0}}, L{package_slash}/IziDialog;"
            f"->show(Landroid/content/Context;)V\n"
            f"    # === END {marker} ===\n"
        )

    method_body = "".join(lines[start:end])
    if marker in method_body:
        log_msg(log, "[!] Инъекция уже присутствует — пропуск")
        return True

    insert_at = None
    for i in range(start, end):
        if "invoke-super" in lines[i]:
            insert_at = i + 1
            break

    if insert_at is None:
        for i in range(start + 1, end):
            stripped = lines[i].strip()
            if stripped and not stripped.startswith("."):
                insert_at = i
                break

    if insert_at is None:
        log_msg(log, "[!] Не удалось найти место вставки")
        return False

    lines.insert(insert_at, inject_block)

    with open(activity_path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)

    log_msg(log, f"[+] Пропатчено: {activity_path}")
    log_msg(log, f"    Метод: {sig.strip()}")
    return True


def build_apk(output_name, log):
    run_cmd(f'apktool b "{OUTPUT_DIR}" -o "{output_name}"', log)


KEYSTORE_TYPE = "JKS"
KEYSTORE_PASS = "android"
KEY_ALIAS = "iziapk"


def ensure_keystore(log):
    keystore = DIRS["assets"] / "iziapk.keystore"
    legacy = SCRIPT_DIR / "iziapk.keystore"
    if not keystore.is_file() and legacy.is_file():
        shutil.move(str(legacy), str(keystore))
    if keystore.is_file():
        try:
            run_cmd(
                f'keytool -list -keystore "{keystore}" -storepass {KEYSTORE_PASS} '
                f"-storetype {KEYSTORE_TYPE}",
                log,
            )
            return keystore
        except RuntimeError:
            log_msg(log, "[!] Keystore повреждён — пересоздаю...")
            keystore.unlink(missing_ok=True)

    run_cmd(
        f'keytool -genkey -v -keystore "{keystore}" -alias {KEY_ALIAS} '
        f"-keyalg RSA -keysize 2048 -validity 10000 "
        f"-storetype {KEYSTORE_TYPE} "
        f"-storepass {KEYSTORE_PASS} -keypass {KEYSTORE_PASS} "
        f'-dname "CN=IZIAPK, OU=IZIAPK, O=IZIAPK, L=City, ST=State, C=RU"',
        log,
    )
    log_msg(log, f"[+] Keystore создан ({KEYSTORE_TYPE})")
    return keystore


def sign_apk(apk_path, log):
    keystore = ensure_keystore(log)

    apksigner = find_tool("apksigner")
    if apksigner:
        cmd = (
            f'"{apksigner}" sign --ks "{keystore}" '
            f"--ks-pass pass:{KEYSTORE_PASS} --key-pass pass:{KEYSTORE_PASS} "
            f"--ks-key-alias {KEY_ALIAS} "
            f"--v1-signing-enabled true --v2-signing-enabled true "
            f'"{apk_path}"'
        )
        if KEYSTORE_TYPE != "JKS":
            cmd = cmd.replace(
                f'--ks-pass pass:{KEYSTORE_PASS}',
                f"--ks-type {KEYSTORE_TYPE} --ks-pass pass:{KEYSTORE_PASS}",
            )
        run_cmd(cmd, log)
        log_msg(log, "[+] APK подписан (apksigner)")
        return True

    uber = SCRIPT_DIR / "uber-apk-signer.jar"
    if not uber.is_file():
        found = sorted(SCRIPT_DIR.glob("uber-apk-signer*.jar"))
        if found:
            uber = found[0]
    if uber.is_file():
        run_cmd(
            f'java -jar "{uber}" -a "{apk_path}" --overwrite '
            f"--allowResign",
            log,
        )
        log_msg(log, "[+] APK подписан (uber-apk-signer)")
        return True

    log_msg(log, "[!] Подписчик не найден — подпишите APK вручную")
    return False


def zipalign_apk(apk_path, log):
    zipalign = find_tool("zipalign")
    if not zipalign:
        log_msg(log, "[!] zipalign не найден — пропуск")
        return

    aligned = apk_path + ".aligned"
    run_cmd(f'"{zipalign}" -f -p 4 "{apk_path}" "{aligned}"', log)
    os.replace(aligned, apk_path)
    log_msg(log, "[+] APK выровнен (zipalign)")


def normalize_telegram_url(url):
    url = (url or "").strip()
    if url.startswith("@"):
        return f"https://t.me/{url[1:]}"
    if url.startswith("t.me/"):
        return f"https://{url}"
    return url


def process_apk(apk_input, telegram_url, log, progress=None, index=0, total=1):
    try:
        telegram_url = normalize_telegram_url(telegram_url)
        ensure_dirs()
        cleanup_temp()
        ensure_apktool(log)

        prefix = f"[{index}/{total}] " if total > 1 else ""
        if progress:
            progress(5, f"{prefix}Проверка файла...")
        if not os.path.isfile(apk_input):
            raise RuntimeError("APK-файл не существует")

        if progress:
            progress(10, f"{prefix}Декомпиляция...")
        decompile(apk_input, log)

        if progress:
            progress(25, f"{prefix}Манифест...")
        package, version, launcher = get_manifest_info(log)
        if not package:
            raise RuntimeError("Не удалось определить package из манифеста")

        package_slash = package.replace(".", "/")

        if progress:
            progress(35, f"{prefix}Добавление smali...")
        write_smali_files(package_slash, telegram_url, log)

        if progress:
            progress(50, f"{prefix}Патч activity...")
        activity = find_launcher_smali(launcher, log)
        if not patch_launcher_activity(activity, package_slash, log):
            raise RuntimeError("Не удалось внедрить вызов диалога")

        if progress:
            progress(70, f"{prefix}Сборка APK...")
        final_apk = str(DIRS["temp"] / "game_modified.apk")
        build_apk(final_apk, log)

        if progress:
            progress(85, f"{prefix}Выравнивание и подпись...")
        zipalign_apk(final_apk, log)
        sign_apk(final_apk, log)

        base_name = os.path.splitext(os.path.basename(apk_input))[0]
        out_name = FINAL_NAME_TEMPLATE.format(game_name=base_name, version=version)
        out_path = DIRS["output"] / out_name
        if out_path.is_file():
            out_path.unlink()
        shutil.move(final_apk, str(out_path))

        cleanup_temp(log)

        if progress:
            progress(100, f"{prefix}Готово!")
        log_msg(log, f"[+] Успех! → {out_path}")
        return str(out_path)

    except Exception as exc:
        log_msg(log, f"[!] ОШИБКА ({os.path.basename(apk_input)}): {exc}")
        cleanup_temp(log)
        return None


def process_multiple(apk_list, telegram_url, log, progress=None):
    results = []
    total = len(apk_list)
    for i, apk in enumerate(apk_list, 1):
        log_msg(log, f"\n{'='*50}")
        log_msg(log, f"[*] Обработка {i}/{total}: {os.path.basename(apk)}")
        log_msg(log, f"{'='*50}")
        result = process_apk(apk, telegram_url, log, progress, i, total)
        results.append((apk, result))
    return results


# ═══════════════════════════════════════════════════════════════
#  GUI
# ═══════════════════════════════════════════════════════════════
class InjectorApp:
    COLORS = {
        "bg": "#0f1419",
        "panel": "#1a2332",
        "accent": "#1E88E5",
        "accent2": "#00BCD4",
        "text": "#e8edf3",
        "muted": "#8b9cb3",
        "input_bg": "#243044",
    }

    def __init__(self, root):
        self.root = root
        self.running = False
        root.title("IZIAPK Injector")
        root.geometry("760x640")
        root.resizable(False, False)
        root.configure(bg=self.COLORS["bg"])

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.TFrame", background=self.COLORS["bg"]
        )
        style.configure(
            "Panel.TFrame", background=self.COLORS["panel"]
        )
        style.configure(
            "Title.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["accent2"],
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Sub.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Panel.TLabel",
            background=self.COLORS["panel"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=(16, 8),
        )
        style.configure(
            "TProgressbar",
            troughcolor=self.COLORS["input_bg"],
            background=self.COLORS["accent2"],
            thickness=8,
        )

        main = ttk.Frame(root, style="Dark.TFrame", padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main,
            text="IZIAPK INJECTOR",
            style="Title.TLabel",
        ).pack(anchor=tk.W)
        ttk.Label(
            main,
            text="Автоматическая вставка диалога подписки в APK",
            style="Sub.TLabel",
        ).pack(anchor=tk.W, pady=(0, 16))

        panel = ttk.Frame(main, style="Panel.TFrame", padding=16)
        panel.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(
            panel, text="APK-файлы (можно несколько):", style="Panel.TLabel"
        ).pack(anchor=tk.W)

        list_row = ttk.Frame(panel, style="Panel.TFrame")
        list_row.pack(fill=tk.X, pady=(6, 8))

        self.apk_listbox = tk.Listbox(
            list_row,
            height=4,
            font=("Segoe UI", 9),
            bg=self.COLORS["input_bg"],
            fg=self.COLORS["text"],
            selectbackground=self.COLORS["accent"],
            relief=tk.FLAT,
            bd=6,
        )
        self.apk_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        btn_col = ttk.Frame(list_row, style="Panel.TFrame")
        btn_col.pack(side=tk.RIGHT)

        for text, cmd, color in [
            ("+ Добавить", self.add_apks, self.COLORS["accent"]),
            ("- Убрать", self.remove_apk, "#455A64"),
            ("Очистить", self.clear_apks, "#455A64"),
        ]:
            tk.Button(
                btn_col, text=text, command=cmd,
                bg=color, fg="white", relief=tk.FLAT,
                padx=10, pady=4, cursor="hand2",
            ).pack(fill=tk.X, pady=2)

        ttk.Label(
            panel, text="Готовые APK → папка output/", style="Panel.TLabel",
        ).pack(anchor=tk.W, pady=(0, 4))

        ttk.Label(
            panel, text="Telegram-канал (URL):", style="Panel.TLabel"
        ).pack(anchor=tk.W)

        self.tg_var = tk.StringVar(value=TELEGRAM_URL)
        tg_entry = tk.Entry(
            panel,
            textvariable=self.tg_var,
            font=("Segoe UI", 10),
            bg=self.COLORS["input_bg"],
            fg=self.COLORS["text"],
            insertbackground=self.COLORS["text"],
            relief=tk.FLAT,
            bd=6,
        )
        tg_entry.pack(fill=tk.X, pady=(6, 0))

        self.progress = ttk.Progressbar(
            main, orient=tk.HORIZONTAL, mode="determinate", length=680
        )
        self.progress.pack(fill=tk.X, pady=(4, 10))

        self.status_var = tk.StringVar(value="Готов к работе")
        ttk.Label(
            main,
            textvariable=self.status_var,
            style="Sub.TLabel",
        ).pack(anchor=tk.W)

        self.start_btn = tk.Button(
            main,
            text="▶  ЗАПУСТИТЬ ИНЪЕКЦИЮ",
            command=self.start,
            bg=self.COLORS["accent2"],
            fg="#0f1419",
            activebackground="#26C6DA",
            activeforeground="#0f1419",
            relief=tk.FLAT,
            font=("Segoe UI", 12, "bold"),
            padx=20,
            pady=10,
            cursor="hand2",
        )
        self.start_btn.pack(pady=12)

        log_frame = ttk.Frame(main, style="Dark.TFrame")
        log_frame.pack(fill=tk.BOTH, expand=True)

        log_toolbar = ttk.Frame(log_frame, style="Dark.TFrame")
        log_toolbar.pack(fill=tk.X)

        copy_btn = tk.Button(
            log_toolbar,
            text="📋 Копировать лог",
            command=self.copy_log,
            bg="#2d333b",
            fg="#e6edf3",
            activebackground="#3d444d",
            activeforeground="#e6edf3",
            relief=tk.FLAT,
            font=("Segoe UI", 9),
            padx=10,
            pady=4,
            cursor="hand2",
        )
        copy_btn.pack(anchor=tk.E, pady=(0, 4))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            font=("Consolas", 9),
            bg="#0a0e14",
            fg="#7ee787",
            insertbackground="#7ee787",
            relief=tk.FLAT,
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def copy_log(self):
        content = self.log_text.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_var.set("Лог скопирован в буфер обмена")

    def add_apks(self):
        paths = filedialog.askopenfilenames(
            title="Выберите APK (можно несколько)",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")],
        )
        existing = set(self.apk_listbox.get(0, tk.END))
        for p in paths:
            if p and p not in existing:
                self.apk_listbox.insert(tk.END, p)

    def remove_apk(self):
        sel = self.apk_listbox.curselection()
        for i in reversed(sel):
            self.apk_listbox.delete(i)

    def clear_apks(self):
        self.apk_listbox.delete(0, tk.END)

    def get_apk_list(self):
        return list(self.apk_listbox.get(0, tk.END))

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def set_progress(self, val, text=""):
        self.progress["value"] = val
        if text:
            self.status_var.set(text)
        self.root.update_idletasks()

    def start(self):
        if self.running:
            return

        apks = self.get_apk_list()
        telegram = normalize_telegram_url(self.tg_var.get().strip())

        if not apks:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один APK-файл.")
            return
        missing = [a for a in apks if not os.path.isfile(a)]
        if missing:
            messagebox.showerror(
                "Ошибка",
                "Некоторые файлы не найдены:\n" + "\n".join(missing),
            )
            return
        if "t.me/" not in telegram:
            messagebox.showwarning(
                "Внимание",
                "Укажите ссылку на Telegram-канал.\n"
                "Примеры: https://t.me/iziapk  или  @iziapk",
            )
            return

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.log_text.delete("1.0", tk.END)
        self.progress["value"] = 0
        self.log(f"[INFO] Старт обработки {len(apks)} APK...")
        self.log(f"[INFO] auto_inject.py build: FIX-6 (двухцветный layout: чёрный верх + белый низ)")
        ensure_dirs()
        threading.Thread(
            target=self._worker, args=(apks, telegram), daemon=True
        ).start()

    def _worker(self, apks, telegram):
        results = process_multiple(apks, telegram, self.log, self.set_progress)
        self.running = False
        self.start_btn.config(state=tk.NORMAL)

        ok = [r for _, r in results if r]
        fail = len(results) - len(ok)

        if ok and not fail:
            self.status_var.set("Готово!")
            messagebox.showinfo(
                "Успех",
                f"Обработано: {len(ok)} APK\n\n"
                f"Папка: {DIRS['output']}\n\n"
                "Диалог появится через 2 сек после загрузки игры.\n"
                "Закрыть можно только кнопкой «ПОДПИСАТЬСЯ».",
            )
        elif ok:
            self.status_var.set(f"Готово: {len(ok)}, ошибок: {fail}")
            messagebox.showwarning(
                "Частично",
                f"Успешно: {len(ok)}\nОшибок: {fail}\n\n"
                f"Смотрите лог. Готовые APK в {DIRS['output']}",
            )
        else:
            self.status_var.set("Ошибка")
            messagebox.showerror("Ошибка", "Ни один APK не обработан. Смотрите лог.")


def main():
    ensure_dirs()
    if len(sys.argv) >= 2:
        tg = sys.argv[-1] if sys.argv[-1].startswith(("http", "@", "t.me")) else TELEGRAM_URL
        apks = [a for a in sys.argv[1:] if a.endswith(".apk")]
        if not apks:
            print("[!] Укажите APK: python auto_inject.py file1.apk [file2.apk ...] [telegram_url]")
            sys.exit(1)
        results = process_multiple(apks, tg, print, None)
        sys.exit(0 if all(r for _, r in results) else 1)

    root = tk.Tk()
    InjectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
