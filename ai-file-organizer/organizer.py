import os
import json
import shutil
from openai import OpenAI
from genericpath import isfile

#MAX_LENGTH = 50                             #文件列表最大长度为50，即50个文件为一批
MAX_LENGTH = 10                              #没有那么多文件，先用10个一批模拟，后续文件较多时只要修改这个常数值就行

#用 Python 读取目标文件夹里的所有文件
def get_files(folder):              #folder 文件夹  listdir 列出目录  directory 目录
    """拿到文件夹里所有的文件（不包含子文件夹）"""
    files = []
    for name in os.listdir(folder):         #列出文件夹里的所有的东西
        path = os.path.join(folder, name)   #拼出完整路径

        if os.path.isfile(path):            #只要文件，跳过文件夹
            files.append(name)
    return files


#先试试能不能拿到列表
folder = r"C:\Users\Administrator\Desktop\测试"     #路径前面那个 r 要注意，它表示“后面的斜杠不当转义符处理”，Windows 路径加上它最省心。
print(get_files(folder))


client = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

#让 AI 判断文件该归哪类
def classify(files):
    """把一批文件名交给 AI，返回 {文件名：类别} 的字典"""  #关键设计有两个：用 JSON 拿结构化结果，以及一次批量处理，而不是一个文件问一次。

    #把文件名拼成一段文本
    file_list = "\n".join(files)                    #批量写入列表，有个换行问题，解决方法："\n".join(files)
    print("file_list：", file_list)

    #注意提示词里的要求写得很死：类别只能是固定的七种，格式必须严格。
    prompt = f"""你是一个文件整理助手。请根据下面的文件名，判断每个文件属于哪个类别。
类别只能是：图片、文档、视频、音频、代码、压缩包、其他。

严格按照以下 JSON 格式输出，不要输出任何其他内容：
{{"文件名1": "类别", "文件名2": "类别"}}

文件名列表：
{file_list}"""  #把隐性要求变成显性要求，类别限制住，AI 才不会给你发明出“临时文件”“重要资料”这种没法建文件夹的名字。

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content

    #清理 AI 可能加的代码块标记（Day9讲过的坑）
    text = text.strip().removeprefix("```json").removesuffix("```").strip()     #见底部 Python 字符串方法详解注释

    return json.loads(text)                          #转成 Python 字典


#收尾：移动文件
def organize(folder, mapping, dry_run = True):       # dry_run 先定为True，进行预演模式，用户确定后再改为 False，正式运行移动文件功能。
    """按判断结果把文件移进对应的子文件夹"""
    """dry_run = True 时只打印计划，不动文件"""

    total = len(mapping)

    #for filename, category in mapping.items():       #Python 字典 items() 函数作用：以列表返回可遍历的(键, 值)元组数组。
    for i, (filename, category) in enumerate(mapping.items(), 1):       #enumerate() 函数作用见底部注释     此处start = 1，起始索引为 1
        ##……移动文件的代码不变……
        #print(f"[{i}/{total}]处理完成")
        src = os.path.join(folder, filename)         #拼出完整的文件路径

        if not os.path.exists(src):                  #文件可能已经不在了，跳过
            continue

        dst_dir = os.path.join(folder, category)     #根据类别确定子文件夹
        os.makedirs(dst_dir, exist_ok=True)          #文件夹不存在就建，已存在也不报错

        if dry_run:                                  #加一个“预演模式”：以后用户跑的时候，先看一眼预演结果，觉得对再把 dry_run 改成 False 才真执行。
            print(f"[预演] {filename} 将移动到 {category}/")
        else:
            #……真正移动的代码……
            shutil.move(src, os.path.join(dst_dir, filename))   #用 shutil.move 而不是 os.rename，前者能跨磁盘移动，更通用。
            print(f"{filename} -> {category}/")
            #……移动文件的代码不变……
            print(f"[{i}/{total}]处理完成")            #加进度显示，如：[1/10]处理完成


#拼起来跑一遍,主流程就是一个流水线：
if __name__ == "__main__":  #if __name__ == '__main__'的意思是：当.py文件被直接运行时，if __name__ == '__main__'之下的代码块将被运行；当.py文件以模块形式被导入时，if __name__ == '__main__'之下的代码块不被运行。
    folder = r"C:\Users\Administrator\Desktop\测试"   #路径前面那个 r 要注意，它表示“后面的斜杠不当转义符处理”，Windows 路径加上它最省心。

    #给整段流程加上异常处理
    try:
        files = get_files(folder)
        if not files:
            print("这个文件夹里没有文件！")
        else:
            print(f"发现 {len(files)} 个文件，正在交给 AI 分类……")

            #防止因文件过多，一次性传给 AI 的文件名列表太长，这边加个循环，分批次传给 AI 操作
            while len(files) > MAX_LENGTH:
                files_cut = files[:MAX_LENGTH]
                files = files[MAX_LENGTH:]
                mapping = classify(files_cut)
                organize(folder, mapping)
                continue
            while len(files) <= MAX_LENGTH:
                mapping = classify(files)
                organize(folder, mapping)
                break
            print("整理完成！")
    except Exception as e:
        print(f"出错了：{e}")
        print("文件没有被移动，你放心")


    #mapping = classify(files)
    #organize(folder, mapping)
    #print("整理完成！")





# for-in 循环：
# in 表达从（字符串、序列等）依次取值，称为遍历。for-in 遍历的对象必须为可迭代对象。

# for-in 的语法结构：
# for 自定义变量 in可迭代对象：
# 循环体

#当循环体内不需要用到自定义变量，可将自定义变量改为下划线，使用range（）来代表循环的次数：
#for _ in range(5):
#    print('我爱学习')      #输出5行 我爱学习



#'\n'.join(files)用法解析：'\'是转义字符，'\n'在字符串中表示产生一个换行操作。
#.join()的用法是将括号中的参数（本例是files列表）中的各项进行连接，返回一个字符串。
#其实'\n'.join(files)中的'\n'就好比一个桥梁把files列表中的每个元素连接起来，并且返回成一个字符串。只不过这里的'\n'是一个转义字符，换行。



# Python 字符串方法详解：
#1. 切片（Slicing）：切片是一种基本的字符串操作方法，它可以按照一定条件从列表或者元组中取出部分元素。
'''
s = ' hello '
s = s[:]
print(s) # hello
s = ' hello '
s = s[3:8]
print(s) # llo
'''
#2. strip() 方法：strip() 方法用于移除字符串头尾指定的字符（默认为空格或换行符）或字符序列。
'''
s = ' hello '.strip()
print(s) # hello
s = '###hello###'.strip()
print(s) # ###hello###
s = '###hello###'.strip('#')
print(s) # hello
'''
#3. lstrip() 方法：lstrip() 方法用于移除字符串左侧指定的字符（默认为空格或换行符）或字符序列。
'''
s = ' hello '.lstrip()
print(s) # hello
s = 'Arthur: three!'.lstrip('Arthur: ')
print(s) # ee!
'''
#4. rstrip() 方法：rstrip() 方法用于移除字符串右侧指定的字符（默认为空格或换行符）或字符序列。
'''
s = ' hello '.rstrip()
print(s) # hello
'''
#5. removeprefix() 方法：removeprefix() 方法是 Python 3.9 中的一个新方法，用于移除字符串的前缀。
'''
s = 'Arthur: three!'.removeprefix('Arthur: ')
print(s) # three!
'''
#6. removesuffix() 方法：removesuffix() 方法是 Python 3.9 中的一个新方法，用于移除字符串的后缀。
'''
s = 'HelloPython'.removesuffix('Python')
print(s) # Hello
'''
#7. replace() 方法：replace() 方法用于把字符串中的内容替换成指定的内容。
'''
s = 'string methods in python'.replace(' ', '-')
print(s) # string-methods-in-python
s = 'string methods in python'.replace(' ', '')
print(s) # stringmethodsinpython
'''
#8. re.sub() 方法：re.sub() 方法是 Python 的正则表达式方法，用于替换字符串中的内容。
'''
import re
s = 'string methods in python'
s = re.sub(' ', '-', s)
print(s) # string-methods-in-python
'''



# 在Python，我们经常会编写if __name__ == '__main__' 这么一段代码，这段代码该怎么来理解？这段代码的功能理解如下：
# 一个python的文件有两种使用的方法：作用一，直接作为脚本执行。作用二，import到其他的python脚本中被调用（模块重用）执行。
# if __name__ == '__main__': 的作用就是控制这两种情况执行代码的过程，在if __name__ == '__main__': 下的代码只有
# 在第一种情况下（即文件作为脚本直接执行）才会被执行，而import到其他脚本中是不会被执行的。


#在Python中，.items()是字典（dict）对象的一个非常实用的方法，它允许我们同时遍历字典的键和值。
#.items()方法返回一个包含字典所有键值对的视图对象。每个键值对以元组(key, value)的形式存在。
#这个方法让我们能够在单个循环中同时访问字典的键和值，而不需要分别获取它们。
#例如：dict = {'老大':'15岁', '老二':'14岁', '老三':'2岁'}
#print(dict.items())    #输出结果：dict_items([('老大', '15岁'), ('老二', '14岁'), ('老三', '2岁')])


# enumerate() 函数的主要作用是将一个可迭代的对象（如列表、元组或字符串等）转换为一个枚举对象。该枚举对象包含了原可迭代对象中每个元素的索引和值。
# enumerate() 函数的基本语法如下：
# enumerate(iterable, start=0) 
# 参数详解：
# iterable：任何可迭代对象（如列表、元组、字符串、range 等）。
# start（可选）: 枚举起始序号（索引的起始值），默认为0，也可以设置其他数值。
# 总结：enumerate 返回一个枚举对象（iterator），每次迭代生成一个包含 (索引, 元素) 的元组。

