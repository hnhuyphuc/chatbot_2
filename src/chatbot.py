import os
from dotenv import load_dotenv
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from supabase import create_client, Client

# Tải biến môi trường
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

class Chatbot:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Vui lòng cung cấp SUPABASE_URL và SUPABASE_KEY trong file .env")

        # 1. Khởi tạo các thành phần cần thiết
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # 2. Kết nối tới Vector Store trên Supabase
        self.vector_store = SupabaseVectorStore(
            client=supabase_client,
            embedding=embeddings,
            table_name="documents",
            query_name="match_documents"
        )
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        # 3. Định nghĩa các câu trả lời và prompt mẫu
        self.NOT_FOUND_IN_SYLLABUS = "Tôi không tìm thấy thông tin về điều này trong tài liệu."
        
        self.rag_prompt = PromptTemplate.from_template(
            "You are an AI assistant for answering questions about the ISTQB syllabus.\n"
            "Answer the question based ONLY on the context provided below.\n"
            f"If the context does not contain the answer, reply with exactly this phrase: '{self.NOT_FOUND_IN_SYLLABUS}'\n\n"
            "Context: {context}\n\n"
            "Question: {question}\n\n"
            "Helpful Answer:"
        )
        
        self.general_prompt = PromptTemplate.from_template("Answer the following question concisely: {question}")

    def search_in_syllabus(self, question):
        """
        Chỉ tìm kiếm câu trả lời trong giáo trình (Supabase).
        Trả về kết quả nếu tìm thấy, ngược lại trả về None.
        """
        retrieved_docs = self.retriever.invoke(question)

        if retrieved_docs:
            context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            rag_chain = (self.rag_prompt | self.llm | StrOutputParser())
            answer_text = rag_chain.invoke({"context": context, "question": question})

            if self.NOT_FOUND_IN_SYLLABUS not in answer_text:
                # Tìm thấy câu trả lời hợp lệ trong ngữ cảnh
                sources = [doc.metadata for doc in retrieved_docs]
                return {"answer": answer_text, "sources": sources}
        
        # Nếu không tìm thấy tài liệu hoặc LLM không tìm thấy câu trả lời
        return None

    def search_with_openai_and_learn(self, question):
        """
        Lấy câu trả lời từ OpenAI và thực hiện tính năng tự học.
        """
        general_chain = self.general_prompt | self.llm | StrOutputParser()
        answer_text = general_chain.invoke({"question": question})

        # --- TÍNH NĂNG TỰ HỌC ---
        try:
            print("INFO: Adding new knowledge to the database with 'pending' status...")
            new_content = f"Question: {question}\nAnswer: {answer_text}"
            new_metadata = {"source": "OpenAI_Generated_Q&A", "status": "pending"}
            
            self.vector_store.add_texts(
                texts=[new_content],
                metadatas=[new_metadata]
            )
            print("INFO: Successfully added new knowledge with 'pending' status.")
        except Exception as e:
            print(f"ERROR: Could not add new knowledge to database: {e}")
        # --- KẾT THÚC TÍNH NĂNG TỰ HỌC ---

        return {
            "answer": answer_text,
            "sources": [{"source": "OpenAI", "page": None}] 
        }
