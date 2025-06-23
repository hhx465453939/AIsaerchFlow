from langchain.prompts import PromptTemplate

def get_optimized_prompt(user_input):
    template = """请将以下用户输入优化为适合AI搜索的高效查询：\n用户输入：{user_input}\n优化后查询："""
    prompt = PromptTemplate.from_template(template)
    return prompt.format(user_input=user_input) 