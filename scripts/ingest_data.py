import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv()

DATA_PATH = "data/"
DB_PATH = "vector_store/"

def create_vector_db():
    print("Bắt đầu tải tài liệu từ các file PDF...")
    loader = PyPDFDirectoryLoader(DATA_PATH)
    documents = loader.load()
    print(f"Đã tải thành công {len(documents)} trang.")

    print("Bắt đầu chia nhỏ văn bản...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    print(f"Đã chia văn bản thành {len(chunks)} chunks.")

    print("Bắt đầu tạo cơ sở dữ liệu vector...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(DB_PATH)
    print(f"Hoàn tất! Cơ sở dữ liệu vector đã được lưu tại: {DB_PATH}")

if __name__ == "__main__":
    create_vector_db()