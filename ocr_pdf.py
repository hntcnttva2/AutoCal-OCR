from langchain_community.document_loaders import PyPDFLoader

def extract_text_from_pdf(file_path="lich_hop.pdf"):
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    text = "\n".join([d.page_content for d in docs])
    return text

if __name__ == "__main__":
    print(extract_text_from_pdf())
