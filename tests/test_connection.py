import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# from langfuse.callback import CallbackHandler

# 加载 .env 环境变量
load_dotenv()

def test_connection():
    print("Testing connection to Aliyun Qwen via ChatOpenAI class...")
    
    # 1. 验证环境变量是否加载
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("MODEL_NAME")
    
    print(f"URL: {base_url}")
    print(f"Model: {model_name}")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment.")
        return

    # 2. 初始化 Langfuse Handler (用于追踪)
    # 确保本地 Langfuse 服务开启，或者注释掉这一部分如果无法连接
    try:
        from langfuse.callback import CallbackHandler
        langfuse_handler = CallbackHandler()
        callbacks = [langfuse_handler]
        print("Langfuse handler initialized.")
    except Exception as e:
        print(f"Warning: Langfuse init failed (is it running?), proceeding without it. Error: {e}")
        callbacks = []

    # 3. 初始化 ChatOpenAI
    # 关键点：使用 base_url 指向阿里云
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.7,
        callbacks=callbacks,
        # 显式传递参数以确保正确，虽然环境变量也会自动生效
        openai_api_key=api_key,
        openai_api_base=base_url
    )

    # 4. 发送请求
    try:
        print("\nSending request...")
        response = llm.invoke("你好，你是谁？请简短回答。")
        print("\nResponse from Qwen:")
        print("-" * 20)
        print(response.content)
        print("-" * 20)
        print("\nTest Passed! ✅")
    except Exception as e:
        print(f"\nTest Failed! ❌\nError: {e}")

if __name__ == "__main__":
    test_connection()
