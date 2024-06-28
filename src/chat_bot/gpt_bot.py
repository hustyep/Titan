from openai import OpenAI

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key="sk-Zk93Fj2L42qG428b73OVM8i6AZFxOxrfQldAda31K0kAAigv",
    base_url="https://api.chatanywhere.tech/v1"
    # base_url="https://api.chatanywhere.cn/v1"
)

def gpt_35_api(messages: list):
    """为提供的对话消息创建新的回答

    Args:
        messages (list): 完整的对话消息
    """
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=messages)
    answer = completion.choices[0].message.content
    print(answer)
    return answer


def gpt_35_api_stream(messages: list):
    """为提供的对话消息创建新的回答 (流式传输)

    Args:
        messages (list): 完整的对话消息
    """
    stream = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")


def answer_gm(question: str):
    messages = [
        {
            "role": "system",
            "content": "you're a maplestory player, and you like this game very much. "
        },
        {
            'role': 'user',
            'content': question + ' short in 5 words'
        },
    ]
    return gpt_35_api(messages)


if __name__ == '__main__':
    answer_gm('what do you want if you have a wish?')
    
    # 非流式调用
    # gpt_35_api(messages)
    # 流式调用
    # gpt_35_api_stream(messages)
