import tabula
import PyPDF2
import re
import pandas as pd


class C6BANK:
    def __init__(self, file_path):
        self.file_path = file_path

    def structure_conta_corrente_pdf(self):
        with open(self.file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            pdf_reader.decrypt('4738')

            number_of_pages = len(pdf_reader.pages)

            page = pdf_reader.pages[1]
            header_text = page.extract_text()
        
        padrao = re.compile(r'([A-Z\s]+)\s+([A-Z]{2})\s+(\d{5}-\d{3})')

        correspondencia = padrao.search(header_text[header_text.index('Conta:'):].split('\n')[3])

        if correspondencia:
            cidade = correspondencia.group(1).strip()
            uf = correspondencia.group(2)
            cep = correspondencia.group(3)
        else:
            print('ERROR - padrão cidade, estado e cep não econtrado!')

        text_to_number = header_text[header_text.index('Conta:'):].split('\n')[4]

        banco_origem = 'C6'
        agencia = header_text[:4]
        conta = header_text[header_text.index('Agência'):].split(':')[1].strip()[:14]
        ts_extracao = header_text[:header_text.index('Pág')][-19:]
        cpf = header_text[header_text.index('Conta:'):].split('\n')[1][-14:]
        nome = header_text[header_text.index('Conta:'):].split('\n')[1][:-14].strip()
        endereco = header_text[header_text.index('Conta:'):].split('\n')[2]
        numero = text_to_number[:text_to_number.index('Categoria')]

        df_pdf = pd.DataFrame()

        for i in range(1, number_of_pages + 1):
            try:
                if i == 1:
                    tables = tabula.read_pdf(r'..\..\data\raw\extrato-da-sua-conta-01HNSZ3CCN9762VAW33HHZ868P.pdf', password='4738',
                                            pages=i,
                                            relative_area=True,
                                            relative_columns=True,
                                            area=[27, 0, 95, 100],
                                            columns=[10, 62, 69, 81, 83, 96])
                    
                    df_temp = tables[0]
                else:
                    tables = tabula.read_pdf(r'..\..\data\raw\extrato-da-sua-conta-01HNSZ3CCN9762VAW33HHZ868P.pdf', password='4738',
                                            pages=i,
                                            pandas_options={'header': None},
                                            relative_area=True,
                                            relative_columns=True,
                                            area=[21, 0, 95, 100],
                                            columns=[10, 62, 69, 81, 83, 96])
                    
                    df_temp = tables[0]
                    df_temp.columns = ['DATA', 'DESCRIÇÃO', 'DOC', 'VALOR', 'D/C', 'VALOR.1']

                df_pdf = pd.concat([df_pdf, df_temp])
            except:
                print(f'WARNING - The PDF has {i-1} page(s). If not, the job might not have executed successfully.')
                break
                
        df_pdf = df_pdf[~df_pdf['DESCRIÇÃO'].str.contains(r'BANCO C6 S.A. - AV. NOVE', case=False)]
        df_pdf = df_pdf[~df_pdf['DESCRIÇÃO'].str.contains(r'%', case=False)]
        df_pdf = df_pdf[~df_pdf['DESCRIÇÃO'].str.contains(r'SALDO', case=False)]
        df_pdf = df_pdf[~df_pdf['DESCRIÇÃO'].str.contains(r'TOTAL', case=False)]
        df_pdf = df_pdf[~df_pdf['DESCRIÇÃO'].str.contains(r'JUROS', case=False)]
        df_pdf = df_pdf[~df_pdf['DESCRIÇÃO'].str.contains(r'LIMITE', case=False)]

        df_pdf = df_pdf.drop(columns=['DOC', 'VALOR.1']).reset_index(drop=True)

        df_pdf['banco_origem'] = banco_origem 
        df_pdf['agencia'] = agencia
        df_pdf['conta'] = conta
        df_pdf['ts_extracao'] = ts_extracao 
        df_pdf['cpf'] = cpf
        df_pdf['nome'] = nome
        df_pdf['endereco'] = endereco 
        df_pdf['numero'] = numero
        df_pdf['cidade'] = cidade 
        df_pdf['uf'] =  uf
        df_pdf['cep'] = cep

        print(f'INFO - {df_pdf.info()}')
        return df_pdf