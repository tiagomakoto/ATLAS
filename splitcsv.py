import pandas as pd

def split_csv(file_path, chunk_size=120):
    # Lê o arquivo original usando o delimitador detectado (;)
    df = pd.read_csv(file_path, sep=';')
    
    # Calcula o número total de arquivos necessários
    num_chunks = (len(df) // chunk_size) + (1 if len(df) % chunk_size != 0 else 0)
    
    for i in range(num_chunks):
        start_row = i * chunk_size
        end_row = start_row + chunk_size
        
        # Fatia o dataframe
        chunk = df.iloc[start_row:end_row]
        
        # Gera o nome do arquivo de saída
        output_file = f'split_part_{i+1}.csv'
        
        # Salva mantendo o cabeçalho e o delimitador original
        chunk.to_csv(output_file, index=False, sep=';')
        print(f'Criado: {output_file}')

split_csv('csvcsv.csv')