from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

DB_PATH = "vector_store/"

class Chatbot:
    def __init__(self):
        # 1. Tải Vector DB
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)

        # 2. Khởi tạo LLM
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        
        # 3. Ngưỡng điểm để xác định độ liên quan. Càng thấp càng liên quan.
        self.SCORE_THRESHOLD = 0.9

        # 4. Định nghĩa các câu trả lời và prompt mẫu
        self.NOT_FOUND_IN_SYLLABUS = "Tôi không tìm thấy thông tin về điều này trong tài liệu."
        
        # Prompt cho RAG (Case 1 & 3)
        self.rag_prompt = PromptTemplate.from_template(
            "You are an AI assistant for answering questions about the ISTQB syllabus.\n"
            "Answer the question based ONLY on the context provided below.\n"
            f"If the context does not contain the answer, reply with exactly this phrase: '{self.NOT_FOUND_IN_SYLLABUS}'\n\n"
            "Context: {context}\n\n"
            "Question: {question}\n\n"
            "Helpful Answer:"
        )
        
        # Prompt cho trường hợp hỏi đáp tổng quát (Case 2)
        self.general_prompt = PromptTemplate.from_template("Answer the following question concisely: {question}")

    def answer(self, question):
        """
        Phân luồng câu trả lời theo logic mới:
        1. Luôn tìm kiếm trong giáo trình trước.
        2. Nếu không liên quan, mới dùng kiến thức chung của OpenAI.
        """
        # BƯỚC 1: LUÔN TÌM KIẾM TRONG GIÁO TRÌNH TRƯỚC
        docs_with_scores = self.db.similarity_search_with_score(question, k=5)
        
        # Mặc định là không tìm thấy tài liệu liên quan
        is_relevant = False
        if docs_with_scores:
            # Lấy điểm của tài liệu liên quan nhất
            best_score = docs_with_scores[0][1]
            if best_score < self.SCORE_THRESHOLD:
                is_relevant = True

        if is_relevant:
            # TRƯỜNG HỢP 1 hoặc 3: Câu hỏi có vẻ liên quan đến giáo trình
            context = "\n\n".join([doc.page_content for doc, score in docs_with_scores])
            
            # SỬA LỖI: Định nghĩa chain một cách chính xác
            rag_chain = (
                self.rag_prompt
                | self.llm
                | StrOutputParser()
            )
            # SỬA LỖI: Gọi chain với dữ liệu đầu vào là một dictionary
            answer_text = rag_chain.invoke({"context": context, "question": question})
            
            # Kiểm tra xem LLM có thực sự tìm thấy câu trả lời trong ngữ cảnh không
            if self.NOT_FOUND_IN_SYLLABUS in answer_text:
                # Case 3: Thuộc giáo trình nhưng không tìm thấy thông tin cụ thể
                return {"answer": self.NOT_FOUND_IN_SYLLABUS, "sources": []}
            else:
                # Case 1: Tìm thấy trong giáo trình
                sources = [doc.metadata for doc, score in docs_with_scores]
                return {"answer": answer_text, "sources": sources}
        else:
            # TRƯỜNG HỢP 2: Câu hỏi không liên quan đến giáo trình -> Dùng OpenAI
            general_chain = self.general_prompt | self.llm | StrOutputParser()
            answer_text = general_chain.invoke({"question": question})

            return {
                "answer": answer_text,
                "sources": [{"source": "OpenAI", "page": None}] 
            }
