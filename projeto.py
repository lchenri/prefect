import prefect_aws.s3
import yfinance as yf
from datetime import datetime, timedelta
from prefect import task, flow
import os
from prefect import flow
from prefect.artifacts import create_link_artifact
import boto3
from botocore.exceptions import NoCredentialsError
from prefect_aws.s3 import S3Bucket
from prefect.variables import Variable
import traceback
# O código abaixo é um fluxo Prefect que baixa dados de ações do Yahoo Finance, os particiona por data,
# os salva localmente e os carrega em um bucket S3.

s3_bucket_block = S3Bucket.load("modelagemdenegocio")

def upload_to_s3(local_file: str, s3_path: str) -> str:
    try:
        # Utiliza o método do bloco para fazer upload do arquivo local para o S3.
        s3_bucket_block.upload_from_path(
            from_path=local_file,
            to_path=s3_path,
        )
        url = f"https://{s3_bucket_block.bucket_name}.s3.amazonaws.com/{s3_path}"
        return url
    except Exception as e:
        print("Erro ao fazer upload:", e)
        return None


def get_date_ranges():
    end_date = datetime.now() + timedelta()
    start_date = end_date - timedelta(days=7)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

@task(retries=3, retry_delay_seconds=5, log_prints=True)
def download_and_partition(tickers):
    start_date, end_date = get_date_ranges()
    partioned = {}

    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date)
            partioned[ticker] = df
            print(f"Dados do {ticker} baixados com sucesso")
        except Exception as exception:
            print(f"Download de {ticker} falhou com o motivo: {exception}")
            traceback.print_exc()

    return partioned


# Salvar dados particionados localmente
@task(retries=3, retry_delay_seconds=5, log_prints=True)
def save_local_partitions(data, base_path="stock_data"):
    local_links = {}
    for ticker, df in data.items():
        try:
            ticker = ticker.lower()
            df = df.reset_index()
            for date, daily_df in df.groupby(df['Date'].dt.date if 'Date' in df.columns else df.index.date):
                date_str = date.strftime('%Y-%m-%d')
                path = os.path.join(
                    base_path,
                    ticker.lower(),
                    str(date.year),
                    f"{date.month:02d}",
                    f"{date.day:02d}"
                )
                os.makedirs(path, exist_ok=True)

                file_path = os.path.join(path, f"{ticker}_{date_str}.csv")
                daily_df.drop(columns=['Date']).to_csv(file_path, index=False)
                ticker = ticker.lower()
                # Cria artifact para cada arquivo
                create_link_artifact(
                    key=f"local-{ticker}-{date_str}",
                    link=file_path,
                    description=f"Dados locais de {ticker} em {date_str}"
                )

                local_links.setdefault(ticker, []).append(file_path)
        except Exception as e:
            print(f"Erro ao salvar {ticker}: {e}")
            traceback.print_exc()

    return local_links


# Upload particionado para S3
@task(retries=3, retry_delay_seconds=5, log_prints=True)
def upload_partitions_to_s3(data):
    s3_links = {}

    for ticker, df in data.items():
        try:
            ticker = ticker.lower()
            df = df.reset_index()  # Adiciona a data como coluna
            for date, daily_df in df.groupby(df['Date'].dt.date if 'Date' in df.columns else df.index.date):
                date_str = date.strftime('%Y-%m-%d')
                # Salva temporariamente
                temp_path = f"temp_{ticker}_{date_str}.csv"
                daily_df.drop(columns=['Date']).to_csv(temp_path, index=False)

                # Path no S3
                s3_path = f"stock_data/{ticker}/{date.year}/{date.month:02d}/{date.day:02d}/{ticker}_{date_str}.csv"

                # Upload
                url = upload_to_s3(temp_path, s3_path)
                print(f"Upload de {ticker} em {date_str} para {url}")
                if url:
                    # Cria artifact para o S3
                    create_link_artifact(
                        key=f"s3-{ticker}-{date_str}",
                        link=url,
                        description=f"Link S3 para {ticker} em {date_str}"
                    )
                    s3_links.setdefault(ticker, []).append(url)

                # Limpeza
                os.remove(temp_path)
        except Exception as e:
            print(f"Erro no upload de {ticker}: {e}")
            traceback.print_exc()

    return s3_links

@flow
def stock_workflow():
    tickers = Variable.get("tickers", default=["AAPL"])
    # Baixa e particiona dados
    partitioned_data = download_and_partition(tickers)
    # Salva localmente
    local_links = save_local_partitions(partitioned_data)
    # Upload para S3
    s3_links = upload_partitions_to_s3(partitioned_data)
    return {"local": local_links, "s3": s3_links}

# if __name__ == '__main__':
#   stock_workflow.serve(
#   name="stock-workflow",
#   tags=["checkpoint1"],
#   cron="0 * * * *",
#   )

if __name__ == "__main__":
    flow.from_source(
        source="https://github.com/prefecthq/demo.git",
        entrypoint="flow.py:my_flow",
    ).deploy(
        name="test-managed-flow",
        work_pool_name="my-managed-pool",
    )

