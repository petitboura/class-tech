"""Tests des outils root (palier root).

Sans telephone : les fonctions pures (parse, formater, valider) sont
testees avec des sorties Android realistes figees ici, et les outils
eux-memes avec un telephone simule (doublures de preparer_root et
executer_root, jamais d'ADB reel : interdiction d'executer un outil
root contre un telephone, meme en lecture). Chaque reponse d'outil
porte la marque non teste (voir pont_root). Demande mcp installe
(import du serveur). Depuis backend/ :
`pytest tests/test_outils_root.py` (ou `python tests/test_outils_root.py`).
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")

from core.outils_root_acces import (  # noqa: E402
    deviner_gestionnaire_root,
    formater_infos_root,
    formater_verif_acces,
    parse_modules_magisk,
)
from core.outils_root_batterie import (  # noqa: E402
    formater_batterie_brute,
    formater_temperatures,
    parse_sysfs_dict,
    parse_thermal,
)
from core.outils_root_corrections import (  # noqa: E402
    DOSSIERS_CRASH,
    commande_redemarrage,
    formater_dalvik,
    formater_nettoyage,
    formater_redemarrage,
    formater_trim,
    parse_du,
    parse_ls_restes,
    parse_trim,
)
from core.outils_root_firmware import (  # noqa: E402
    formater_firmware,
    formater_validation_slot,
    parse_getprop_firmware,
    parse_version_noyau,
    slot_valide,
)
from core.outils_root_partitions import (  # noqa: E402
    formater_integrite,
    formater_partitions,
    parse_byname,
    parse_df,
    parse_getprop_simple,
    parse_mounts,
)
from core.outils_root_processus import (  # noqa: E402
    formater_processus,
    formater_wakelocks,
    parse_top,
    parse_wakelocks,
)
from core.outils_root_systeme import (  # noqa: E402
    est_texte_affichable,
    formater_erreurs_noyau,
    formater_fichier_systeme,
    formater_liste_fichiers,
    formater_paniques,
    ligne_est_erreur,
    masquer_mac,
    parse_dmesg_erreurs,
    parse_ls_la,
    parse_paniques,
)
from core.pont_root import (  # noqa: E402
    AVERTISSEMENT_NON_TESTE,
    chemin_interdit,
    chemin_lecture_valide,
    commande_root,
    marquer_non_teste,
    message_root_absent,
    parse_uid_root,
)
from core.registre_outils import (  # noqa: E402
    OUTILS_PALIER_ROOT,
    OUTILS_ROOT_ACTIFS,
    OUTILS_SENSIBLES,
)


def test_commande_root_protegee():
    cmd = commande_root("ls -la /system")
    assert cmd.startswith("su -c ")
    assert "/system" in cmd


def test_parse_uid_root():
    assert parse_uid_root("uid=0(root) gid=0(root)") == 0
    assert parse_uid_root("uid=2000(shell) gid=2000(shell)") == 2000
    assert parse_uid_root("") is None
    assert parse_uid_root("pas d'uid ici") is None


def test_marquer_non_teste():
    texte = marquer_non_teste("Quelque chose.")
    assert "non teste sur appareil roote" in texte
    assert texte.startswith("Quelque chose.")
    assert marquer_non_teste("") == AVERTISSEMENT_NON_TESTE


def test_message_root_absent_sans_tiret_double():
    assert "--" not in message_root_absent("detail")
    assert "roote" in message_root_absent()


def test_chemin_lecture_valide():
    assert chemin_lecture_valide("/system/build.prop")
    assert chemin_lecture_valide("/data/adb/modules")
    assert chemin_lecture_valide("/proc/version")
    assert not chemin_lecture_valide("/sdcard/photo.jpg")
    assert not chemin_lecture_valide("/system/../data")
    assert not chemin_lecture_valide("relatif/system")
    assert not chemin_lecture_valide("/system/a;rm -rf /")
    assert not chemin_lecture_valide("")


def test_gestionnaire_root():
    assert "Magisk" in deviner_gestionnaire_root("magisk\nmodules\n")
    assert "KernelSU" in deviner_gestionnaire_root("ksu\nmodules\n")
    assert deviner_gestionnaire_root("") == "gestionnaire inconnu"


def test_modules_magisk():
    dossiers, modules = parse_modules_magisk(
        "zygisk_lsposed\nsystemless_hosts\n",
        "id=zygisk_lsposed\nname=LSPosed\nid=systemless_hosts\nname=Hosts\n",
    )
    assert dossiers == ["zygisk_lsposed", "systemless_hosts"]
    assert modules["zygisk_lsposed"] == "LSPosed"
    assert parse_modules_magisk("", "") == ([], {})


def test_formater_verif_acces():
    ok = formater_verif_acces(0, "Magisk probable", "Enforcing")
    assert "uid 0" in ok and "Magisk" in ok and "Enforcing" in ok
    assert "roote" in formater_verif_acces(2000, "", "").lower() or \
        "root" in formater_verif_acces(2000, "", "").lower()
    assert "--" not in ok


def test_formater_infos_root():
    texte = formater_infos_root("27.0:MAGISKSU", ["mod_a"], {"mod_a": "Mod A"})
    assert "27.0" in texte and "mod_a" in texte
    assert "aucun module" in formater_infos_root("", [], {})


def test_parse_ls_la():
    entrees = parse_ls_la(
        "total 100\n"
        "drwxr-xr-x 10 root root 4096 2026-01-01 00:00 app\n"
        "-rw-r--r-- 1 root root 12345 2026-01-01 00:00 build.prop\n"
        "ligne bizarre\n"
    )
    assert ("app", 4096, "drwxr-xr-x") in entrees
    assert ("build.prop", 12345, "-rw-r--r--") in entrees
    assert parse_ls_la("") == []


def test_formater_liste_fichiers():
    texte = formater_liste_fichiers("/system", [("a", 2048, "drwxr-xr-x")])
    assert "/system" in texte and "2 Ko" in texte
    assert "illisible" in formater_liste_fichiers("/x", [])
    assert "--" not in texte


def test_fichier_systeme():
    assert not est_texte_affichable("abc\x00def")
    assert est_texte_affichable("ro.build.id=AP1A\n")
    assert "binaire" in formater_fichier_systeme("/f", "a\x00b", False)
    assert "vide" in formater_fichier_systeme("/f", "  \n", False)
    plein = formater_fichier_systeme("/f", "ligne1\nligne2", True)
    assert "ligne1" in plein and "suite non affichee" in plein


def test_dmesg_erreurs():
    lignes, lues = parse_dmesg_erreurs(
        "[Mon Jan 1 00:00:01 2026] binder: transaction failed\n\n"
        "[Mon Jan 1 00:00:02 2026] init: service failed\n"
    )
    assert len(lignes) == 2
    assert lues == 2
    texte = formater_erreurs_noyau(lignes, 100, lues)
    assert "2 ligne" in texte and "binder" in texte
    assert "Aucune erreur" in formater_erreurs_noyau([], 100, 50)
    assert "illisible" in formater_erreurs_noyau([], 100, 0)


def test_paniques():
    traces = parse_paniques([
        ("/proc/last_kmsg", ""),
        ("/sys/fs/pstore/console-ramoops", "Kernel panic VFS\n"),
    ])
    assert len(traces) == 1
    assert "1 trace" in formater_paniques(traces)
    assert "Aucune trace" in formater_paniques([])


def test_parse_df():
    df = parse_df(
        "Filesystem 1K-blocks Used Available Use% Mounted on\n"
        "/dev/block/dm-0 100G 60G 40G 60% /data\n"
        "tmpfs 4G 0 4G 0% /dev\n"
    )
    assert len(df) == 2
    assert df[0][5] == "/data"
    assert parse_df("") == []


def test_parse_mounts():
    montages = parse_mounts(
        "/dev/block/dm-0 / ext4 ro,seclabel 0 0\n"
        "/dev/block/dm-1 /data ext4 rw,seclabel 0 0\n"
    )
    assert montages["/"] == ("ext4", "ro,seclabel")
    assert montages["/data"][1].startswith("rw")


def test_parse_byname():
    byname, total = parse_byname(
        "lrwxrwxrwx 1 root root 16 2026-01-01 00:00 boot -> ../../sda1\n"
        "lrwxrwxrwx 1 root root 16 2026-01-01 00:00 system -> ../../dm-0\n"
    )
    assert ("boot", "../../sda1") in byname
    assert len(byname) == 2
    assert total == 2


def test_formater_partitions():
    df = [("/dev/x", "100G", "60G", "40G", "60%", "/data")]
    texte = formater_partitions(df, {"/": ("ext4", "ro,seclabel")}, [("boot", "x")])
    assert "/data" in texte and "40G" in texte
    assert "lecture seule" in texte
    assert "--" not in texte
    assert "illisibles" in formater_partitions([], {}, [])


def test_formater_integrite():
    props = {
        "ro.boot.verifiedbootstate": "green",
        "ro.boot.flash.locked": "1",
        "ro.boot.vbmeta.device_state": "locked",
    }
    texte = formater_integrite(props, "... androidboot.verifiedbootstate=green ...",
                               {"/": ("ext4", "ro,seclabel")})
    assert "verifie" in texte and "verrouille" in texte
    louche = formater_integrite(
        {"ro.boot.flash.locked": "0", "ro.debuggable": "1"}, "",
        {"/system": ("ext4", "rw,seclabel")})
    assert "DEVERROUILLE" in louche and "mise au point" in louche
    assert "illisible" in formater_integrite({}, "", {})


def test_parse_sysfs_dict():
    valeurs = parse_sysfs_dict(
        "voltage_now:4100000\ncurrent_now:-500000\ntemp:320\n"
    )
    assert valeurs == {
        "voltage_now": "4100000", "current_now": "-500000", "temp": "320",
    }
    assert parse_sysfs_dict("") == {}


def test_formater_batterie_brute():
    texte = formater_batterie_brute({
        "voltage_now": "4100000", "current_now": "-500000", "temp": "320",
        "charge_counter": "3000000", "charge_full": "4000000",
        "charge_full_design": "5000000", "cycle_count": "350",
        "capacity": "75", "health": "Good", "technology": "Li-ion",
    })
    assert "4.10 V" in texte
    assert "500 mA (decharge probable)" in texte
    assert "32.0 C" in texte
    assert "3000 mAh" in texte
    assert "80 %" in texte
    assert "350 cycles" in texte
    assert "--" not in texte
    assert "illisible" in formater_batterie_brute({})


def test_parse_thermal():
    zones = parse_thermal(
        "/sys/class/thermal/thermal_zone0/type:battery\n"
        "/sys/class/thermal/thermal_zone1/type:cpu\n",
        "/sys/class/thermal/thermal_zone0/temp:32000\n"
        "/sys/class/thermal/thermal_zone1/temp:65000\n",
    )
    assert zones[0][1] == "cpu" and zones[0][2] == 65.0
    assert len(zones) == 2
    texte = formater_temperatures(zones)
    assert "cpu 65.0 C" in texte
    assert "illisibles" in formater_temperatures([])


def test_parse_getprop_firmware():
    infos = parse_getprop_firmware(
        "[ro.build.version.release]: [15]\n"
        "[ro.boot.slot_suffix]: [_a]\n"
        "ligne ignoree\n"
    )
    assert infos == {
        "ro.build.version.release": "15", "ro.boot.slot_suffix": "_a",
    }
    assert parse_getprop_firmware("") == {}
    assert parse_getprop_simple("[a]: [b]") == {"a": "b"}


def test_parse_version_noyau():
    noyau = parse_version_noyau(
        "Linux version 6.1.0-android (build@...) #1 SMP ...\n"
    )
    assert noyau.startswith("Linux version 6.1.0-android")
    assert parse_version_noyau("") == ""


def test_formater_firmware():
    texte = formater_firmware(
        {"ro.product.model": "Pixel 8", "ro.build.version.release": "15",
         "ro.build.version.security_patch": "2026-10-05",
         "ro.boot.bootloader": "boot-1.0", "gsm.version.baseband": "base-2.0",
         "ro.boot.slot_suffix": "_a", "ro.build.date": "1 oct 2026"},
        "Linux version 6.1.0",
    )
    assert "Pixel 8" in texte and "Android 15" in texte
    assert "slot actif _a" in texte and "6.1.0" in texte
    assert "--" not in texte
    assert "illisible" in formater_firmware({}, "")


def test_formater_validation_slot():
    assert "rien a valider" in formater_validation_slot("", False)
    assert "marque comme bon" in formater_validation_slot("_a", True)
    assert "non valide" in formater_validation_slot("_b", False, "refuse")


def test_parse_top():
    processus = parse_top(
        "Tasks: 300 total\n"
        " 1234 u0_a100 45% S 10 1G 200M fg u0_a100 com.gros.jeu\n"
        " 56 root 2% S 5 100M 10M fg root system_server\n"
        "ligne ignoree\n"
    )
    assert processus[0][4] == "com.gros.jeu" and processus[0][1] == 45.0
    assert len(processus) == 2
    texte = formater_processus(processus, 10)
    assert "com.gros.jeu (45 % CPU)" in texte
    assert "illisibles" in formater_processus([], 10)


def test_parse_wakelocks():
    annonce, noms = parse_wakelocks(
        "Wake Locks: size=2\n"
        "  PARTIAL_WAKE_LOCK 'MyApp:Sync' (uid=10123, pid=456)\n"
        "  PARTIAL_WAKE_LOCK 'AudioMix' (uid=1041, pid=78)\n"
    )
    assert annonce == 2
    assert noms == ["MyApp:Sync", "AudioMix"]
    texte = formater_wakelocks(annonce, noms)
    assert "2 verrou" in texte and "MyApp:Sync" in texte
    assert "dort bien" in formater_wakelocks(0, [])


def test_parse_du():
    tailles = parse_du("12M\t/data/tombstones\n4.0K\t/data/anr\nligne bizarre\n")
    assert tailles["/data/tombstones"] == "12M"
    assert parse_du("") == {}


def test_formater_nettoyage_dalvik():
    vides = {d: [] for d in DOSSIERS_CRASH}
    texte = formater_nettoyage({"/data/tombstones": "12M"}, vides)
    assert "supprimes" in texte and "12M" in texte
    partiel = dict(vides)
    partiel["/data/anr"] = ["trace_01.txt"]
    assert "partiel" in formater_nettoyage({}, partiel).lower()
    assert "resiste" in formater_nettoyage({}, partiel)
    assert "--" not in texte
    dalvik = formater_dalvik("800M", [])
    assert "800M" in dalvik and "Redemarre" in dalvik
    assert "partiel" in formater_dalvik("", ["x"]).lower()


def test_parse_trim():
    resultats = parse_trim("/data: 123456789 bytes trimmed\n/cache: 0 bytes trimmed\n")
    assert resultats[0] == ("/data", 123456789)
    assert parse_trim("rien ici") == []
    texte = formater_trim(resultats, True)
    assert "/data" in texte and "Mo" in texte
    assert "refusee" in formater_trim([], False, "x")
    assert "gain illisible" in formater_trim([], True)


def test_commande_redemarrage():
    assert commande_redemarrage("normal") == "reboot"
    assert commande_redemarrage("recovery") == "reboot recovery"
    assert commande_redemarrage("bootloader") == "reboot bootloader"
    assert commande_redemarrage("usine") is None
    assert "redemarrage" in formater_redemarrage("normal", True).lower()
    assert "recovery" in formater_redemarrage("recovery", True)
    assert "boutons" in formater_redemarrage("recovery", True)
    assert "boutons" in formater_redemarrage("bootloader", True)
    rate = formater_redemarrage("normal", False, "x")
    assert "incertain" in rate and "ecran" in rate


def test_registre_root_coherent():
    assert len(OUTILS_PALIER_ROOT) == 19
    assert set(OUTILS_PALIER_ROOT) <= OUTILS_SENSIBLES  # chaque palier ajoute ses sensibles


def _noms_outils_serveur_frais(activer_root):
    """Noms exposes par un serveur importe dans un interpreteur frais.

    En sous-processus : ce fichier importe deja les modules root, ce
    qui les enregistrerait sur l'objet partage du processus courant
    et fausserait le test du garde-fou.
    """
    script = (
        "import asyncio, sys; sys.path.insert(0, '.'); "
        "import core.registre_outils as r; "
        f"r.OUTILS_ROOT_ACTIFS = {activer_root}; "
        "from core.serveur_mcp_diagnostic import mcp_diagnostic; "
        "noms = sorted(o.name for o in asyncio.run(mcp_diagnostic.list_tools())); "
        "print('OUTILS:' + ','.join(noms))"
    )
    termine = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert termine.returncode == 0, termine.stderr[-2000:]
    for ligne in termine.stdout.splitlines():
        if ligne.startswith("OUTILS:"):
            return set(n for n in ligne[len("OUTILS:"):].split(",") if n)
    raise AssertionError(f"marqueur OUTILS absent : {termine.stdout[-500:]}")


def test_garde_fou_root_desactive_par_defaut():
    assert OUTILS_ROOT_ACTIFS is False
    noms = _noms_outils_serveur_frais(False)
    for nom in OUTILS_PALIER_ROOT:
        assert nom not in noms, f"{nom} expose malgre le garde-fou"
    assert "lire_batterie" in noms
    assert "revoquer_permission" in noms
    assert not [n for n in noms if n.startswith("root_")]


def test_garde_fou_root_expose_si_active():
    noms = _noms_outils_serveur_frais(True)
    for nom in OUTILS_PALIER_ROOT:
        assert nom in noms, f"{nom} absent du serveur actif"


def test_outils_root_importables_directement():
    import core.outils_root_acces as acces
    import core.outils_root_batterie as batterie
    import core.outils_root_corrections as corrections
    import core.outils_root_firmware as firmware
    import core.outils_root_partitions as partitions
    import core.outils_root_processus as processus
    import core.outils_root_systeme as systeme
    modules = (acces, batterie, corrections, firmware, partitions,
               processus, systeme)
    trouves = set()
    for module in modules:
        for nom in OUTILS_PALIER_ROOT:
            if callable(getattr(module, nom, None)):
                trouves.add(nom)
    assert trouves == set(OUTILS_PALIER_ROOT)


def test_chemins_interdits():
    prives = [
        "/data/data/com.exemple/base.db",
        "/data/user/0/com.exemple/f",
        "/data/media/0/DCIM/photo.jpg",
        "/data/misc/wifi/WifiConfigStore.xml",
        "/dev/block/mmcblk0",
        "/dev/input/event0",
        "/proc/kcore",
        "/proc/kallsyms",
        "/sys/kernel/debug/tracing",
    ]
    for chemin in prives:
        assert chemin_interdit(chemin), chemin
        assert not chemin_lecture_valide(chemin), chemin
    assert not chemin_interdit("/data/adb/modules")
    assert not chemin_interdit("/databackup/x")
    assert chemin_lecture_valide("/data/adb/modules")
    assert chemin_lecture_valide("/sys/class/power_supply/battery/voltage_now")


def test_gestionnaire_sans_faux_positifs():
    assert deviner_gestionnaire_root("super\nresult\nmodules\n") == \
        "gestionnaire inconnu"
    assert deviner_gestionnaire_root("su\nmodules\n") == \
        "binaire su present, gestionnaire inconnu"
    assert "Magisk" in deviner_gestionnaire_root("magisk.db\nmodules\n")
    assert "KernelSU" in deviner_gestionnaire_root("ksu\nservice.d\n")


def test_modules_magisk_sans_name():
    _dossiers, modules = parse_modules_magisk(
        "mod_a\nmod_b\n",
        "id=mod_a\nname=Module A\nid=mod_b\nversion=1\n"
        "id=mod_c\nname=Module C\n",
    )
    assert modules == {
        "mod_a": "Module A", "mod_b": "mod_b", "mod_c": "Module C",
    }


def test_parse_ls_la_liens():
    entrees = parse_ls_la(
        "lrwxrwxrwx 1 root root 11 2026-01-01 00:00 bin -> /system/bin\n"
        "-rw-r--r-- 1 root root 42 2026-01-01 00:00 build.prop\n"
    )
    assert ("bin", 11, "lrwxrwxrwx") in entrees
    assert ("build.prop", 42, "-rw-r--r--") in entrees


def test_ligne_est_erreur():
    assert ligne_est_erreur("[1.2] binder: transaction failed")
    assert ligne_est_erreur("[1.3] BUG: scheduling while atomic")
    assert ligne_est_erreur("[1.4] mmc0: error -110")
    assert ligne_est_erreur("[1.5] init: service 'x' failed")
    assert ligne_est_erreur("[1.6] Kernel panic - not syncing")
    assert not ligne_est_erreur("[1.7] usb: new device connected")
    assert not ligne_est_erreur("debug: terrible state reached")
    assert not ligne_est_erreur("")


def test_masquer_mac():
    assert masquer_mac("wlan0: AA:bb:CC:11:22:33 up") == \
        "wlan0: [adresse masquee] up"
    assert masquer_mac("rien ici") == "rien ici"
    assert masquer_mac("") == ""


def test_paniques_illisibles():
    assert "illisible" in formater_paniques([], 0)
    assert "Aucune trace" in formater_paniques([], 3)
    traces = parse_paniques([
        ("/proc/last_kmsg", "mac AA:BB:CC:DD:EE:FF oops\n"),
    ])
    assert "[adresse masquee]" in traces[0][1]


def test_parse_df_ligne_coupee():
    df = parse_df(
        "Filesystem 1K-blocks Used Available Use% Mounted on\n"
        "/dev/block/mapper/super_partition_tres_longue\n"
        " 100G 60G 40G 60% /data\n"
        "tmpfs 4G 0 4G 0% /dev\n"
    )
    points = [ligne[5] for ligne in df]
    assert "/data" in points and "/dev" in points


def test_byname_tronque_honnete():
    lignes = "".join(
        f"lrwxrwxrwx 1 root root 16 2026-01-01 00:00 part{i} -> ../../sda{i}\n"
        for i in range(50)
    )
    entrees, total = parse_byname(lignes, limite=40)
    assert total == 50 and len(entrees) == 40
    texte = formater_partitions(
        [("/dev/x", "100G", "60G", "40G", "60%", "/data")], {}, (entrees, total)
    )
    assert "50 partition(s)" in texte and "40 premieres" in texte


def test_integrite_partielle_inconnu():
    texte = formater_integrite(
        {"ro.boot.vbmeta.device_state": "locked"}, "",
        {"/": ("ext4", "ro,seclabel")})
    assert "verifie : inconnu" in texte
    assert "chargeur : etat inconnu" in texte
    assert "lecture seule" in texte


def test_batterie_brute_avec_status():
    charge = formater_batterie_brute(
        {"current_now": "-500000", "status": "Charging"})
    assert "(en charge)" in charge
    assert "probable" not in charge
    decharge = formater_batterie_brute(
        {"current_now": "500000", "status": "Discharging"})
    assert "(en decharge)" in decharge
    assert "pleine" in formater_batterie_brute({"status": "Full"})


def test_thermal_aberrante_ignoree():
    zones = parse_thermal(
        "z0/type:cpu\nz1/type:capteur_fou\n",
        "z0/temp:65000\nz1/temp:999000\n",
    )
    assert [z[1] for z in zones] == ["cpu"]
    assert parse_thermal("z/type:x\n", "z/temp:-300000\n") == []


def test_getprop_firmware_filtre():
    infos = parse_getprop_firmware(
        "[ro.build.version.release]: [15]\n"
        "[ro.build.fingerprint]: [marque/modele:15/x]\n"
        "[gsm.sim.operator.alpha]: [Operateur]\n"
    )
    assert infos == {
        "ro.build.version.release": "15",
        "ro.build.fingerprint": "marque/modele:15/x",
    }
    texte = formater_firmware(
        {"ro.product.model": "Pixel 8",
         "ro.build.fingerprint": "marque/modele:15/x"},
        "",
    )
    assert "empreinte marque/modele" in texte


def test_slot_valide():
    assert slot_valide("_a")
    assert slot_valide("_b")
    assert not slot_valide("")
    assert not slot_valide("a")
    assert not slot_valide("_ab")
    assert not slot_valide("[_a]")
    assert not slot_valide(None)


def test_processus_format_inconnu():
    assert "non reconnu" in formater_processus(
        [], 10, "Tasks: 300 total\nPID inconnu\n")
    assert "illisibles" in formater_processus([], 10, "")
    assert "illisibles" in formater_processus([], 10)


def test_parse_ls_restes():
    assert parse_ls_restes("") == []
    assert parse_ls_restes("a.txt\nb.txt\n") == ["a.txt", "b.txt"]


# --- Tests des fonctions outils avec telephone simule (audit A) ---
#
# Aucun ADB reel : preparer_root et executer_root sont remplaces par
# des doublures qui rejouent des sorties Android figees. Interdiction
# d'executer un outil root contre un telephone, meme en lecture.


def _interdire_adb_reel(monkeypatch):
    """Rend tout appel ADB reel impossible en test (audit A).

    Si une doublure oublie un chemin, le test explose au lieu de
    parler a un vrai telephone. Interdiction absolue d'executer un
    outil root ou sensible contre adb reel, meme en lecture.
    """
    def interdit(*args, **kwargs):
        raise AssertionError("appel adb reel interdit en test")

    monkeypatch.setattr("core.pont_adb.executer_adb", interdit)
    monkeypatch.setattr("core.pont_adb.executer_adb_serie", interdit)
    monkeypatch.setattr("core.pont_adb.executer_shell", interdit)


def _simuler_racine(monkeypatch, nom_module, reponses, shell=None):
    """Doublures preparer_root/executer_root (+executer_shell).

    reponses : [(fragment_commande, {"ok","sortie","erreur"})], le
    premier fragment contenu dans la commande gagne. Renvoie la
    liste des commandes recues, dans l'ordre. La doublure est aussi
    installee sur core.pont_root (pour verifier_root, qui appelle
    executer_root depuis son propre module), et tout ADB reel est
    interdit (voir _interdire_adb_reel).
    """
    commandes = []

    def faux_executer(commande, appareil_id, delai=None):
        commandes.append(commande)
        for fragment, reponse in reponses:
            if fragment in commande:
                return dict(reponse)
        return {"ok": False, "sortie": "", "erreur": "commande non simulee"}

    def faux_shell(commande, appareil_id, delai=None):
        commandes.append("shell:" + commande)
        for fragment, reponse in shell or []:
            if fragment in commande:
                return dict(reponse)
        return {"ok": False, "sortie": "", "erreur": "commande non simulee"}

    _interdire_adb_reel(monkeypatch)
    monkeypatch.setattr(nom_module + ".preparer_root", lambda: ("TEST123", None))
    monkeypatch.setattr(nom_module + ".executer_root", faux_executer)
    monkeypatch.setattr("core.pont_root.executer_root", faux_executer)
    if shell is not None:
        monkeypatch.setattr(nom_module + ".executer_shell", faux_shell)
    return commandes


def test_outil_verifier_acces(monkeypatch):
    import core.outils_root_acces as acces
    monkeypatch.setattr(
        "core.outils_root_acces.preparer_appel", lambda: ("TEST123", None))
    commandes = _simuler_racine(monkeypatch, "core.outils_root_acces", [
        ("ls /data/adb", {"ok": True, "sortie": "magisk\nmodules\n", "erreur": ""}),
        ("id", {"ok": True, "sortie": "uid=0(root) gid=0(root)\n", "erreur": ""}),
    ], shell=[("getenforce", {"ok": True, "sortie": "Enforcing\n", "erreur": ""})])
    texte = acces.root_verifier_acces()
    assert "uid 0" in texte and "Magisk" in texte and "Enforcing" in texte
    assert "non teste sur appareil roote" in texte
    assert commandes[0] == "id"


def test_outil_lire_infos_root(monkeypatch):
    import core.outils_root_acces as acces
    _simuler_racine(monkeypatch, "core.outils_root_acces", [
        ("ls /data/adb/modules",
         {"ok": True, "sortie": "mod_a\n", "erreur": ""}),
        ("module.prop",
         {"ok": True, "sortie": "id=mod_a\nname=Mod A\n", "erreur": ""}),
    ], shell=[("su --version",
               {"ok": True, "sortie": "27.0:MAGISKSU\n", "erreur": ""})])
    texte = acces.root_lire_infos_root()
    assert "27.0" in texte and "mod_a" in texte


def test_outil_lister_fichiers(monkeypatch):
    import core.outils_root_systeme as systeme
    _simuler_racine(monkeypatch, "core.outils_root_systeme", [
        ("ls -la", {"ok": True, "sortie":
            "drwxr-xr-x 2 root root 4096 2026-01-01 00:00 app\n"
            "-rw-r--r-- 1 root root 2048 2026-01-01 00:00 build.prop\n",
            "erreur": ""}),
    ])
    texte = systeme.root_lister_fichiers_systeme("/system")
    assert "2 entree(s)" in texte and "build.prop" in texte
    assert "refuse" in systeme.root_lister_fichiers_systeme("/data/media")
    assert "refuse" in systeme.root_lister_fichiers_systeme("/data/data/x")


def test_outil_lire_fichier_tronque_et_refus(monkeypatch):
    import core.outils_root_systeme as systeme
    _simuler_racine(monkeypatch, "core.outils_root_systeme", [
        ("wc -c -l", {"ok": True, "sortie": "25000 300\n", "erreur": ""}),
        ("head -c", {"ok": True, "sortie": "ligne1\nligne2\n", "erreur": ""}),
    ])
    texte = systeme.root_lire_fichier_systeme("/system/build.prop", 2)
    assert "ligne1" in texte and "suite non affichee" in texte
    assert "refuse" in systeme.root_lire_fichier_systeme("/dev/block/mmcblk0")
    assert "invalide" in systeme.root_lire_fichier_systeme("/system/f", 999)


def test_outil_erreurs_noyau_filtre(monkeypatch):
    import core.outils_root_systeme as systeme
    commandes = _simuler_racine(monkeypatch, "core.outils_root_systeme", [
        ("dmesg", {"ok": True, "sortie":
            "[1.0] usb: new device connected\n"
            "[2.0] binder: transaction failed\n"
            "[3.0] mmc0: error -110\n",
            "erreur": ""}),
    ])
    texte = systeme.root_lire_erreurs_noyau()
    assert "2 ligne" in texte and "binder" in texte
    assert "usb" not in texte
    assert "-l " not in commandes[0]
    assert "invalide" in systeme.root_lire_erreurs_noyau("beaucoup")


def test_outil_paniques(monkeypatch):
    import core.outils_root_systeme as systeme
    _simuler_racine(monkeypatch, "core.outils_root_systeme", [
        ("head -c", {"ok": False, "sortie": "", "erreur": "absent"}),
    ])
    assert "illisibles" in systeme.root_lire_paniques_passees()
    _simuler_racine(monkeypatch, "core.outils_root_systeme", [
        ("console-ramoops",
         {"ok": True, "sortie": "Kernel panic - not syncing\n", "erreur": ""}),
        ("head -c", {"ok": False, "sortie": "", "erreur": "absent"}),
    ])
    assert "1 trace" in systeme.root_lire_paniques_passees()


def test_outil_partitions(monkeypatch):
    import core.outils_root_partitions as partitions
    _simuler_racine(monkeypatch, "core.outils_root_partitions", [
        ("df -h", {"ok": True, "sortie":
            "Filesystem 1K-blocks Used Available Use% Mounted on\n"
            "/dev/block/dm-0 100G 60G 40G 60% /data\n", "erreur": ""}),
        ("cat /proc/mounts", {"ok": True, "sortie":
            "/dev/block/dm-0 / ext4 ro,seclabel 0 0\n", "erreur": ""}),
        ("by-name", {"ok": True, "sortie":
            "lrwxrwxrwx 1 root root 16 2026-01-01 00:00 boot -> ../../sda1\n",
            "erreur": ""}),
    ])
    texte = partitions.root_lire_partitions()
    assert "/data" in texte and "lecture seule" in texte and "boot" in texte


def test_outil_integrite(monkeypatch):
    import core.outils_root_partitions as partitions
    _simuler_racine(monkeypatch, "core.outils_root_partitions", [
        ("cat /proc/cmdline", {"ok": True, "sortie":
            "androidboot.verifiedbootstate=green console=tty\n", "erreur": ""}),
        ("cat /proc/mounts", {"ok": True, "sortie":
            "/dev/block/dm-0 / ext4 ro,seclabel 0 0\n", "erreur": ""}),
    ], shell=[("getprop", {"ok": True, "sortie":
        "[ro.boot.flash.locked]: [1]\n", "erreur": ""})])
    texte = partitions.root_verifier_integrite()
    assert "verifie" in texte and "verrouille" in texte


def test_outil_batterie_repli_bms(monkeypatch):
    import core.outils_root_batterie as batterie
    _simuler_racine(monkeypatch, "core.outils_root_batterie", [
        ("power_supply/battery",
         {"ok": False, "sortie": "", "erreur": "cd refuse"}),
        ("power_supply/bms", {"ok": True, "sortie":
            "voltage_now:4100000\ncurrent_now:-500000\nstatus:Charging\n",
            "erreur": ""}),
    ])
    texte = batterie.root_lire_batterie_brute()
    assert "4.10 V" in texte and "(en charge)" in texte


def test_outil_temperatures(monkeypatch):
    import core.outils_root_batterie as batterie
    _simuler_racine(monkeypatch, "core.outils_root_batterie", [
        ("thermal_zone*/type", {"ok": True, "sortie":
            "/sys/class/thermal/thermal_zone0/type:cpu\n", "erreur": ""}),
        ("thermal_zone*/temp", {"ok": True, "sortie":
            "/sys/class/thermal/thermal_zone0/temp:65000\n", "erreur": ""}),
    ])
    assert "cpu 65.0 C" in batterie.root_lire_temperatures()
    assert "invalide" in batterie.root_lire_temperatures(99)


def test_outil_raz_stats_batterie(monkeypatch):
    import core.outils_root_batterie as batterie
    _simuler_racine(monkeypatch, "core.outils_root_batterie", [
        ("batterystats", {"ok": True, "sortie": "", "erreur": ""}),
    ])
    assert "remises a zero" in batterie.root_reinitialiser_stats_batterie()
    _simuler_racine(monkeypatch, "core.outils_root_batterie", [
        ("batterystats", {"ok": False, "sortie": "", "erreur": "refuse"}),
    ])
    assert "non remis" in batterie.root_reinitialiser_stats_batterie()


def test_outil_firmware(monkeypatch):
    import core.outils_root_firmware as firmware
    _simuler_racine(monkeypatch, "core.outils_root_firmware", [
        ("cat /proc/version", {"ok": True, "sortie":
            "Linux version 6.1.0-android (build@hote) #1 SMP\n", "erreur": ""}),
    ], shell=[("getprop", {"ok": True, "sortie":
        "[ro.product.model]: [Pixel 8]\n"
        "[ro.build.version.release]: [15]\n"
        "[ro.boot.slot_suffix]: [_a]\n", "erreur": ""})])
    texte = firmware.root_lire_firmware()
    assert "Pixel 8" in texte and "Android 15" in texte
    assert "slot actif _a" in texte


def test_outil_valider_slot(monkeypatch):
    import core.outils_root_firmware as firmware
    _simuler_racine(monkeypatch, "core.outils_root_firmware", [
        ("bootctl", {"ok": True, "sortie": "", "erreur": ""}),
    ], shell=[("slot_suffix", {"ok": True, "sortie": "_a\n", "erreur": ""})])
    assert "marque comme bon" in firmware.root_valider_slot_demarre()
    _simuler_racine(monkeypatch, "core.outils_root_firmware", [
        ("bootctl", {"ok": True, "sortie": "", "erreur": ""}),
    ], shell=[("slot_suffix", {"ok": True, "sortie": "yaourt\n", "erreur": ""})])
    assert "rien valide" in firmware.root_valider_slot_demarre()
    _simuler_racine(monkeypatch, "core.outils_root_firmware", [
        ("bootctl", {"ok": True, "sortie": "", "erreur": ""}),
    ], shell=[("slot_suffix", {"ok": False, "sortie": "", "erreur": "casse"})])
    assert "Slot illisible" in firmware.root_valider_slot_demarre()


def test_outil_processus(monkeypatch):
    import core.outils_root_processus as processus
    _simuler_racine(monkeypatch, "core.outils_root_processus", [
        ("top -n 1", {"ok": True, "sortie":
            " 1234 u0_a100 45% S 10 1G 200M fg u0_a100 com.gros.jeu\n",
            "erreur": ""}),
    ])
    texte = processus.root_lister_processus()
    assert "com.gros.jeu (45 % CPU)" in texte
    assert "invalide" in processus.root_lister_processus(0)


def test_outil_wakelocks(monkeypatch):
    import core.outils_root_processus as processus
    _simuler_racine(monkeypatch, "core.outils_root_processus", [
        ("dumpsys power", {"ok": True, "sortie":
            "Wake Locks: size=2\n"
            "  PARTIAL_WAKE_LOCK 'MyApp:Sync' (uid=10123, pid=456)\n"
            "  PARTIAL_WAKE_LOCK 'AudioMix' (uid=1041, pid=78)\n",
            "erreur": ""}),
    ])
    texte = processus.root_lire_wakelocks()
    assert "2 verrou" in texte and "MyApp:Sync" in texte


def test_outil_nettoyer_crash_commande_unique(monkeypatch):
    import core.outils_root_corrections as corrections
    commandes = _simuler_racine(monkeypatch, "core.outils_root_corrections", [
        ("du -sh", {"ok": True, "sortie":
            "12M\t/data/tombstones\n4.0K\t/data/anr\n", "erreur": ""}),
        ("rm -rf", {"ok": True, "sortie": "", "erreur": ""}),
        ("ls -A", {"ok": True, "sortie": "", "erreur": ""}),
    ])
    texte = corrections.root_nettoyer_fichiers_crash()
    rms = [c for c in commandes if c.startswith("rm -rf")]
    assert len(rms) == 1
    assert rms[0].count("rm -rf") == 1
    assert " rm " not in rms[0].replace("rm -rf", "")
    assert sum(1 for c in commandes if c.startswith("ls -A")) == 3
    assert "supprimes" in texte and "12M" in texte


def test_outil_nettoyer_crash_partiel(monkeypatch):
    import core.outils_root_corrections as corrections
    _simuler_racine(monkeypatch, "core.outils_root_corrections", [
        ("du -sh", {"ok": True, "sortie": "", "erreur": ""}),
        ("rm -rf", {"ok": True, "sortie": "", "erreur": ""}),
        ("ls -A", {"ok": True, "sortie": "trace_01.txt\n", "erreur": ""}),
    ])
    texte = corrections.root_nettoyer_fichiers_crash()
    assert "partiel" in texte.lower() and "resiste" in texte


def test_outil_dalvik(monkeypatch):
    import core.outils_root_corrections as corrections
    _simuler_racine(monkeypatch, "core.outils_root_corrections", [
        ("du -sh", {"ok": True, "sortie":
            "800M\t/data/dalvik-cache\n", "erreur": ""}),
        ("rm -rf", {"ok": True, "sortie": "", "erreur": ""}),
        ("ls -A", {"ok": True, "sortie": "", "erreur": ""}),
    ])
    texte = corrections.root_vider_cache_dalvik()
    assert "Cache Dalvik vide" in texte and "800M" in texte


def test_outil_trim(monkeypatch):
    import core.outils_root_corrections as corrections
    _simuler_racine(monkeypatch, "core.outils_root_corrections", [
        ("fstrim", {"ok": True, "sortie":
            "/data: 123456789 bytes trimmed\n", "erreur": ""}),
    ])
    assert "Stockage optimise" in corrections.root_forcer_trim()
    _simuler_racine(monkeypatch, "core.outils_root_corrections", [
        ("fstrim", {"ok": False, "sortie": "", "erreur": "refuse"}),
    ])
    assert "refusee" in corrections.root_forcer_trim()


def test_outil_redemarrer(monkeypatch):
    import core.outils_root_corrections as corrections
    assert "acceptees" in corrections.root_redemarrer("usine")
    _simuler_racine(monkeypatch, "core.outils_root_corrections", [
        ("reboot", {"ok": False, "sortie": "", "erreur": "connexion fermee"}),
    ])
    assert "incertain" in corrections.root_redemarrer()
    _simuler_racine(monkeypatch, "core.outils_root_corrections", [
        ("reboot", {"ok": True, "sortie": "", "erreur": ""}),
    ])
    assert "redemarrage" in corrections.root_redemarrer("recovery").lower()


if __name__ == "__main__":
    test_commande_root_protegee()
    test_parse_uid_root()
    test_marquer_non_teste()
    test_message_root_absent_sans_tiret_double()
    test_chemin_lecture_valide()
    test_gestionnaire_root()
    test_modules_magisk()
    test_formater_verif_acces()
    test_formater_infos_root()
    test_parse_ls_la()
    test_formater_liste_fichiers()
    test_fichier_systeme()
    test_dmesg_erreurs()
    test_paniques()
    test_parse_df()
    test_parse_mounts()
    test_parse_byname()
    test_formater_partitions()
    test_formater_integrite()
    test_parse_sysfs_dict()
    test_formater_batterie_brute()
    test_parse_thermal()
    test_parse_getprop_firmware()
    test_parse_version_noyau()
    test_formater_firmware()
    test_formater_validation_slot()
    test_parse_top()
    test_parse_wakelocks()
    test_parse_du()
    test_formater_nettoyage_dalvik()
    test_parse_trim()
    test_commande_redemarrage()
    test_registre_root_coherent()
    test_chemins_interdits()
    test_gestionnaire_sans_faux_positifs()
    test_modules_magisk_sans_name()
    test_parse_ls_la_liens()
    test_ligne_est_erreur()
    test_masquer_mac()
    test_paniques_illisibles()
    test_parse_df_ligne_coupee()
    test_byname_tronque_honnete()
    test_integrite_partielle_inconnu()
    test_batterie_brute_avec_status()
    test_thermal_aberrante_ignoree()
    test_getprop_firmware_filtre()
    test_slot_valide()
    test_processus_format_inconnu()
    test_parse_ls_restes()
    test_garde_fou_root_desactive_par_defaut()
    test_garde_fou_root_expose_si_active()
    test_outils_root_importables_directement()
    # Tests avec telephone simule : mini doublure de monkeypatch.
    import importlib

    class Rustine:
        def setattr(self, cible, valeur):
            module, _, attr = cible.rpartition(".")
            setattr(importlib.import_module(module), attr, valeur)

    rustine = Rustine()
    test_outil_verifier_acces(rustine)
    test_outil_lire_infos_root(rustine)
    test_outil_lister_fichiers(rustine)
    test_outil_lire_fichier_tronque_et_refus(rustine)
    test_outil_erreurs_noyau_filtre(rustine)
    test_outil_paniques(rustine)
    test_outil_partitions(rustine)
    test_outil_integrite(rustine)
    test_outil_batterie_repli_bms(rustine)
    test_outil_temperatures(rustine)
    test_outil_raz_stats_batterie(rustine)
    test_outil_firmware(rustine)
    test_outil_valider_slot(rustine)
    test_outil_processus(rustine)
    test_outil_wakelocks(rustine)
    test_outil_nettoyer_crash_commande_unique(rustine)
    test_outil_nettoyer_crash_partiel(rustine)
    test_outil_dalvik(rustine)
    test_outil_trim(rustine)
    test_outil_redemarrer(rustine)
    print("OK : outils root.")
