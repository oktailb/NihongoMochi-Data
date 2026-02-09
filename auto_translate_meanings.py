#!/usr/bin/python3
import os
import json
import time
import glob
from deep_translator import GoogleTranslator

# Configuration
KANJI_DETAILS_FILE = '../NihongoMochi/shared/src/commonMain/composeResources/files/kanji/kanji_details.json'
SOURCE_MEANINGS_FILE = '../NihongoMochi/shared/src/commonMain/composeResources/files/meanings/meanings_en_rGB.json'
TARGET_FILES_PATTERN = 'langs/*'

LANG_MAP = {
    'ar_SA': 'ar',
    'bn_BD': 'bn',
    'de_DE': 'de',
    'es_ES': 'es',
    'fr_FR': 'fr',
    'in_ID': 'id',
    'it_IT': 'it',
#    'ja_JP': 'ja',
    'ko_KR': 'ko',
    'mn_MN': 'mn',
    'pt_BR': 'pt',
    'ru_RU': 'ru',
    'th_TH': 'th',
    'ua_UA': 'uk',
    'vi_VN': 'vi',
    'zh_CN': 'zh-CN'
}

def load_json(file_path):
    if not os.path.exists(file_path): 
        print(f"Fichier non trouvé: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur chargement {file_path}: {e}")
        return None

def save_json(file_path, data):
    try:
        # Trier les kanjis par ID
        if 'meanings' in data and 'kanji' in data['meanings']:
            data['meanings']['kanji'].sort(key=lambda x: int(x['@id']))
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ Fichier sauvegardé: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Erreur sauvegarde {file_path}: {e}")
        return False

def main():
    print("--- Démarrage de la traduction des Kanjis ---")
    kanji_details = load_json(KANJI_DETAILS_FILE)
    if not kanji_details: 
        print("❌ Impossible de charger kanji_details.json")
        return

    # Indexation id -> character
    kanji_map = {}
    for k in kanji_details.get('kanji_details', {}).get('kanji', []):
        kanji_map[str(k['id'])] = k['character']
    print(f"✅ Indexés: {len(kanji_map)} kanjis de référence")

    source_data = load_json(SOURCE_MEANINGS_FILE)
    if not source_data: 
        print("❌ Impossible de charger le fichier source meanings_en_rGB.json")
        return
    source_kanjis = source_data['meanings']['kanji']
    print(f"✅ Source: {len(source_kanjis)} kanjis à traiter")

    # Lister les fichiers cibles
    target_files = glob.glob(TARGET_FILES_PATTERN)
    print(f"🔍 Fichiers cibles trouvés: {len(target_files)}")
    
    for target_file in target_files:
        print(f"\n📁 Traitement: {target_file}")
        
        if 'en_rGB' in target_file: 
            print("  ⏭️  Fichier source anglais, ignoré")
            continue
            
        locale = os.path.basename(target_file)
        lang = LANG_MAP.get(locale)
        if not lang: 
            print(f"  ⚠️  Locale non supportée: {locale}")
            continue
            
        print(f"  🌐 Langue: {locale} ({lang})")
        
        # Charger les données cibles
        target_data_path = f'{target_file}/meanings.json'
        target_data = load_json(target_data_path)
        
        # Initialiser si nécessaire
        if not target_data:
            target_data = {
                "meanings": {
                    "@locale": locale,
                    "kanji": []
                }
            }
            print(f"  📄 Création d'un nouveau fichier pour {locale}")
        
        # Créer un dictionnaire pour accès rapide
        existing_map = {}
        for k in target_data['meanings'].get('kanji', []):
            existing_map[str(k['@id'])] = k
        
        # Initialiser les traducteurs
        try:
            translator_ja = GoogleTranslator(source='ja', target=lang)
            translator_en = GoogleTranslator(source='en', target=lang)
        except Exception as e:
            print(f"  ❌ Erreur initialisation traducteur: {e}")
            continue
        
        updates = 0
        needs_save = False
        
        for s_kanji in source_kanjis:
            k_id = str(s_kanji['@id'])
            char = kanji_map.get(k_id)
            
            # RAISON 1: Kanji absent de la base de référence
            if not char:
                # print(f"  ⚠️  ID {k_id}: absent de la base de référence")
                continue

            # Obtenir la signification source
            s_meaning_val = s_kanji.get('meaning', [])
            s_list = [s_meaning_val] if isinstance(s_meaning_val, str) else s_meaning_val
            
            # Vérifier si existe déjà
            t_entry = existing_map.get(k_id)
            
            # RAISON 2: Déjà traduit (et différent de l'anglais)
            if t_entry:
                t_val = t_entry.get('meaning', [])
                t_list = [t_val] if isinstance(t_val, str) else t_val
                
                # Normaliser les listes pour comparaison
                def normalize_list(lst):
                    if isinstance(lst, str):
                        return [lst.strip()]
                    return [item.strip() for item in lst if item and str(item).strip()]
                
                s_norm = normalize_list(s_list)
                t_norm = normalize_list(t_list)
                
                # Si la traduction existe et est différente de l'anglais, on saute
                if t_norm and t_norm != s_norm:
                    # print(f"  ✅ ID {k_id} ({char}): déjà traduit")
                    continue
            
            # TRADUCTION
            try:
                print(f"  🔄 Traduction ID {k_id} ({char})... ", end='', flush=True)
                
                # Traduire le caractère du japonais
                main_m = translator_ja.translate(char)
                
                # Traduire les significations de l'anglais
                trans_en_text = translator_en.translate("\n".join(s_list))
                trans_en_list = trans_en_text.split("\n") if trans_en_text else []
                
                # Construire la nouvelle liste de significations
                new_m = []
                if main_m and main_m != char: 
                    new_m.append(main_m.strip().capitalize())
                
                for m in trans_en_list:
                    m_clean = m.strip().capitalize()
                    if m_clean and m_clean not in new_m: 
                        new_m.append(m_clean)
                
                # Déterminer la valeur finale
                if len(new_m) == 0:
                    final_val = ""
                elif len(new_m) == 1:
                    final_val = new_m[0]
                else:
                    final_val = new_m
                
                # Créer ou mettre à jour l'entrée
                new_entry = {"@id": k_id, "meaning": final_val}
                
                if not t_entry:
                    target_data['meanings']['kanji'].append(new_entry)
                    existing_map[k_id] = new_entry
                else:
                    # Trouver l'index et mettre à jour
                    for i, item in enumerate(target_data['meanings']['kanji']):
                        if str(item['@id']) == k_id:
                            target_data['meanings']['kanji'][i] = new_entry
                            existing_map[k_id] = new_entry
                            break
                
                print(f"✅: {final_val}")
                updates += 1
                needs_save = True
                
                # Pause pour éviter de surcharger l'API
                time.sleep(0.3)
                
            except Exception as e:
                print(f"❌ ERREUR: {e}")
                time.sleep(1)  # Pause plus longue en cas d'erreur
        
        # Sauvegarder seulement si des changements ont été faits
        if needs_save and updates > 0:
            print(f"  💾 Sauvegarde de {updates} traduction(s)...")
            if save_json(target_data_path, target_data):
                print(f"  ✅ Terminé: {locale} ({updates} nouveau(x))")
            else:
                print(f"  ❌ Échec de sauvegarde pour {locale}")
        elif updates == 0:
            print(f"  ℹ️  Aucune nouvelle traduction pour {locale}")

if __name__ == "__main__":
    main()
