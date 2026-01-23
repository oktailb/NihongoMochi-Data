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
    'ja_JP': 'ja',
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
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur chargement {file_path}: {e}")
        return None

def save_json(file_path, data):
    try:
        data['meanings']['kanji'].sort(key=lambda x: int(x['@id']))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde {file_path}: {e}")

def main():
    print("--- Démarrage de la traduction des Kanjis ---")
    kanji_details = load_json(KANJI_DETAILS_FILE)
    if not kanji_details: return

    # Indexation id -> character
    kanji_map = {}
    for k in kanji_details.get('kanji_details', {}).get('kanji', []):
        kanji_map[str(k['id'])] = k['character']
    print(f"Indexés: {len(kanji_map)} kanjis de référence (depuis kanji_details.json)")

    source_data = load_json(SOURCE_MEANINGS_FILE)
    if not source_data: return
    source_kanjis = source_data['meanings']['kanji']
    print(f"Source: {len(source_kanjis)} kanjis à traiter (depuis meanings_en_rGB.json)")

    print(f"list glob {glob.glob(TARGET_FILES_PATTERN)}")
    for target_file in glob.glob(TARGET_FILES_PATTERN):
        print(target_file)
        if 'en_rGB' in target_file: continue
        locale = os.path.basename(target_file).replace('langs/', '') #.replace('/meanings.json', '')
        lang = LANG_MAP.get(locale)
        if not lang: continue
            
        print(f"\nLangue: {locale} ({lang})")
        target_data = load_json(f'{target_file}/meanings.json') or {"meanings": {"@locale": locale, "kanji": []}}
        existing = {str(k['@id']): k for k in target_data['meanings'].get('kanji', [])}
        
        translator_ja = GoogleTranslator(source='ja', target=lang)
        translator_en = GoogleTranslator(source='en', target=lang)
        updates = 0
        
        for s_kanji in source_kanjis:
            k_id = str(s_kanji['@id'])
            char = kanji_map.get(k_id)
            
            # RAISON DU SAUT 1: Kanji absent de la base de référence
            if not char:
                continue

            s_meaning_val = s_kanji.get('meaning', [])
            s_list = [s_meaning_val] if isinstance(s_meaning_val, str) else s_meaning_val
            
            t_entry = existing.get(k_id)
            
            # RAISON DU SAUT 2: Déjà traduit (valeur différente de l'anglais)
            if t_entry:
                t_val = t_entry.get('meaning', [])
                t_list = [t_val] if isinstance(t_val, str) else t_val
                if t_list and t_list != s_list:
                    continue

            # TRADUCTION
            try:
                print(f"    Traduction ID {k_id} ({char})... ", end='', flush=True)
                main_m = translator_ja.translate(char)
                trans_en_text = translator_en.translate("\n".join(s_list))
                trans_en_list = trans_en_text.split("\n") if trans_en_text else []
                
                new_m = []
                if main_m and main_m != char: new_m.append(main_m.strip().capitalize())
                for m in trans_en_list:
                    m = m.strip().capitalize()
                    if m and m not in new_m: new_m.append(m)
                
                final_val = new_m if len(new_m) > 1 else (new_m[0] if new_m else "")
                if not t_entry:
                    target_data['meanings']['kanji'].append({"@id": k_id, "meaning": final_val})
                    existing[k_id] = target_data['meanings']['kanji'][-1]
                else:
                    t_entry['meaning'] = final_val
                
                print(f"OK: {final_val}")
                updates += 1
                
                if updates % 100 == 0:
                    save_json(f'{target_file}/meanings.json', target_data)
                    print(f"    [Checkpoint] {updates} kanjis sauvegardés...")
                
                time.sleep(0.2)
            except Exception as e:
                print(f"ERREUR: {e}")
                time.sleep(0.2)

        if updates > 0:
            save_json(f'{target_file}/meanings.json', target_data)
            print(f"  -> Terminé: {target_file} ({updates} nouveaux)")

if __name__ == "__main__":
    main()
