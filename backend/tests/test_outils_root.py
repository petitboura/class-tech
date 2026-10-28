"""Tests des outils root (palier root).

Sans telephone : seules les fonctions pures (parse, formater, valider)
sont testees, avec des sorties Android realistes figees ici. Les outils
eux-memes demandent un telephone roote branché, indisponible ici :
chaque reponse d'outil porte la marque non teste (voir pont_root).
Demande mcp installe (import du serveur). Depuis backend/ :
`pytest tests/test_outils_root.py` (ou `python tests/test_outils_root.py`).
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
    commande_redemarrage,
    formater_dalvik,
    formater_nettoyage,
    formater_redemarrage,
    formater_trim,
    parse_du,
    parse_trim,
)
from core.outils_root_firmware import (  # noqa: E402
    formater_firmware,
    formater_validation_slot,
    parse_getprop_firmware,
    parse_version_noyau,
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
    parse_dmesg_erreurs,
    parse_ls_la,
    parse_paniques,
)
from core.pont_root import (  # noqa: E402
    AVERTISSEMENT_NON_TESTE,
    chemin_lecture_valide,
    commande_root,
    marquer_non_teste,
    message_root_absent,
    parse_uid_root,
)
from core.registre_outils import OUTILS_PALIER_ROOT, OUTILS_SENSIBLES  # noqa: E402
from core.serveur_mcp_diagnostic import mcp_diagnostic  # noqa: E402


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
    lignes = parse_dmesg_erreurs(
        "[Mon Jan 1 00:00:01 2026] binder: transaction failed\n\n"
        "[Mon Jan 1 00:00:02 2026] init: service failed\n"
    )
    assert len(lignes) == 2
    texte = formater_erreurs_noyau(lignes, 100)
    assert "2 ligne" in texte and "binder" in texte
    assert "Aucune erreur" in formater_erreurs_noyau([], 100)


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
    byname = parse_byname(
        "lrwxrwxrwx 1 root root 16 2026-01-01 00:00 boot -> ../../sda1\n"
        "lrwxrwxrwx 1 root root 16 2026-01-01 00:00 system -> ../../dm-0\n"
    )
    assert ("boot", "../../sda1") in byname
    assert len(byname) == 2


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
    assert "500 mA (decharge)" in texte
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
    texte = formater_nettoyage({"/data/tombstones": "12M"}, True)
    assert "supprimes" in texte and "12M" in texte
    assert "rien supprime" in formater_nettoyage({}, False)
    assert "--" not in texte
    dalvik = formater_dalvik("800M", True)
    assert "800M" in dalvik and "Redemarre" in dalvik
    assert "rien supprime" in formater_dalvik("", False)


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
    assert "refuse" in formater_redemarrage("normal", False, "x")


def test_registre_root_coherent():
    assert len(OUTILS_PALIER_ROOT) == 19
    assert set(OUTILS_PALIER_ROOT) <= OUTILS_SENSIBLES  # chaque palier ajoute ses sensibles


def test_outils_root_enregistres_sur_le_serveur():
    outils = asyncio.run(mcp_diagnostic.list_tools())
    noms = {o.name for o in outils}
    for nom in OUTILS_PALIER_ROOT:
        assert nom in noms, f"{nom} absent du serveur"
    for outil in outils:
        if outil.name in OUTILS_PALIER_ROOT:
            assert "root" in (outil.description or "").lower()


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
    test_outils_root_enregistres_sur_le_serveur()
    print("OK : outils root.")
