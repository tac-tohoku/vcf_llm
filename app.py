import pandas as pd
import pysam
import os
import openai
from llama_index.core import VectorStoreIndex

# OpenAI APIキーを設定します
openai.api_key = os.environ["OPENAI_API_KEY"]

# 論文データ読み込み
def read_text_file(snp_name):
    directory_path = f"./text/{snp_name}"
    file_path = os.path.join(directory_path, "data.csv")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    else:
        return None

def load_csv(file_path):
    df = pd.read_csv(file_path)
    df = df.dropna(subset=['Abstract'])  # 'abstract'列にNaNがある行を削除
    texts = df['Abstract'].tolist()
    file_names = df['PubMedURL'].tolist()  # 'PubMedURL'列の内容を読み込む
    return texts, file_names

# CSVファイルの読み込み
snp_list = pd.read_csv("./vcf_files/snp_list.csv")

# VCFファイルの読み込み
vcf = pysam.VariantFile("./vcf_files/dummy_vcf_1.vcf")

# VCFデータをデータフレームに変換
vcf_records = []
for record in vcf:
    record_dict = {
        'CHROM': record.chrom,
        'POS': record.pos,
        'ID': record.id,
        'REF': record.ref,
        'ALT': ','.join(str(alt) for alt in record.alts),
        'QUAL': record.qual,
        'FILTER': ';'.join(record.filter.keys()),
        'INFO': ';'.join(f"{key}={value}" for key, value in record.info.items())
    }
    vcf_records.append(record_dict)
vcf_table = pd.DataFrame(vcf_records)

# ID列でマージ
vcf_pick = pd.merge(vcf_table, snp_list, on="ID")

# 各SNPに対応するテキストファイルの内容を格納するリスト
snp_texts = []

for index, row in vcf_pick.iterrows():
    snp_id = row['ID']
    print(f"Processing SNP: {snp_id}")

    # Read the corresponding text file
    text_content = read_text_file(snp_id)
    if text_content:
        snp_texts.append({'snp_id': snp_id, 'content': text_content})
    else:
        snp_texts.append({'snp_id': snp_id, 'content': 'No text file found'})

#インデックス化して、GPTに読み込ませるデータを軽量化する。（API利用料節約を目的に）
index = VectorStoreIndex.from_documents(snp_texts)

# OpenAIを使用して要約を生成する関数
query_engine = index.as_query_engine()
response = query_engine.query("Please summarize the following text")
print(response)

# 要約結果を格納するリスト
#summarized_texts = []

#for snp_text in snp_texts:
#    if snp_text['content'] != 'No text file found':
#        summary = summarize_text(snp_text['content'])
#        summarized_texts.append({'snp_id': snp_text['snp_id'], 'summary': summary})
#    else:
#        summarized_texts.append({'snp_id': snp_text['snp_id'], 'summary': 'No text file found'})

# 結果を表示
#for summary in summarized_texts:
#    print(f"SNP ID: {summary['snp_id']}")
#    print(f"Summary: {summary['summary']}\n")

