# Cybersecurity High-Quality Dataset (网络安全高质量数据集)

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Dataset Size](https://img.shields.io/badge/Size-2.2GB-green.svg)](https://modelscope.cn/datasets/hcnote/Cybersecurity-Dataset)
[![Data Quality](https://img.shields.io/badge/Quality_Score-%E2%89%A54.5-brightgreen.svg)](https://github.com/yangqi1309134997-coder/DataSanity)

## 概述 | Overview

这是一个经过多次清洗和质量筛选的网络安全领域高质量中英文问答数据集，包含270,271条高质量数据。本数据集基于原始的大型网络安全数据集，使用 **DataSanity** 工具进行严格的数据清洗和质量评估，仅保留得分4.5分及以上的高质量数据，适用于网络安全领域的AI模型训练、知识图谱构建、智能问答系统开发等应用场景。

A high-quality Chinese-English cybersecurity Q&A dataset containing 270,271 carefully curated entries. This dataset is derived from a large-scale cybersecurity corpus and rigorously cleaned using the **DataSanity** tool, with only data scoring 4.5 or higher retained. It is suitable for AI model training, knowledge graph construction, and intelligent QA system development in the cybersecurity domain.

---

## 数据集信息 | Dataset Information

| 属性 | 值 |
|------|-----|
| **文件名称** | cleaned_2026-1-5-Cybersecurity-bigDataset_qualified_qualified.jsonl |
| **文件大小** | 2.2 GB |
| **数据条数** | 270,271 条 |
| **数据格式** | JSONL (JSON Lines) |
| **清洗日期** | 2026-01-05 |
| **质量阈值** | ≥ 4.5/5.0 |
| **语言** | 中文、英文 |
| **原始数据集** | [Cybersecurity-Dataset @ ModelScope](https://modelscope.cn/datasets/hcnote/Cybersecurity-Dataset) |
| **清洗工具** | [DataSanity](https://github.com/yangqi1309134997-coder/DataSanity) |

---

## 数据结构 | Data Structure

每条数据采用 JSONL 格式存储，包含以下字段：

```json
{
  "instruction": "问题或指令内容 | Question or instruction",
  "output": "详细的答案或响应内容 | Detailed answer or response",
  "id": "唯一标识符 (UUID格式) | Unique identifier (UUID format)"
}
```

### 字段说明 | Field Description

- **instruction**: 用户提供的问题、指令或任务描述，涵盖网络安全的各个子领域
- **output**: 针对instruction的高质量答案或解决方案，内容详实、结构清晰
- **id**: 数据的唯一标识符，采用UUID v4格式，便于去重和引用

---

## 数据覆盖领域 | Coverage Areas

本数据集涵盖网络安全领域的广泛主题，包括但不限于：

### 核心安全概念 | Core Security Concepts
- 信息安全三要素（CIA Triad）：机密性、完整性、可用性
- 安全架构设计与原则
- 风险评估与安全治理
- 合规性与标准（ISO 27001、等保2.0等）

### Web安全 | Web Security
- OWASP Top 10 漏洞分析与防护
- SQL注入、XSS、CSRF等常见攻击
- RESTful API安全设计
- HTTP请求走私、Web缓存漏洞
- 安全加固与最佳实践

### 威胁情报与攻防 | Threat Intelligence & Red/Blue Team
- 威胁情报分析与利用
- 攻击链（Kill Chain）与MITRE ATT&CK框架
- 红队测试方法论
- 蓝队防御技术与响应策略
- 持久化机制与检测

### 渗透测试与漏洞利用 | Penetration Testing & Exploitation
- 信息收集与侦察技术
- 漏洞扫描与验证
- 权限提升技术
- 内网渗透与横向移动
- 渗透测试工具使用（SQLMap、爆破工具等）

### 系统与网络安全 | System & Network Security
- Windows/Linux系统安全
- Docker容器安全与逃逸
- 网络流量分析与嗅探
- 防火墙与入侵检测系统
- VPN与远程访问安全

---

## 数据质量保证 | Data Quality Assurance

### 清洗流程 | Cleaning Process

本数据集经过以下清洗步骤：

1. **多轮清洗**: 使用DataSanity工具进行多次迭代清洗，逐步提升数据质量
2. **质量评分**: 每条数据通过多维度评分机制评估（相关性、准确性、完整性、可读性等）
3. **阈值筛选**: 仅保留评分≥4.5分的高质量数据（满分5.0分）
4. **格式标准化**: 统一JSONL格式，确保字段完整性和数据一致性
5. **去重处理**: 基于UUID和内容相似度去除重复数据

### 质量特征 | Quality Characteristics

- ✅ **准确性高**: 答案经过严格的质量评分机制验证
- ✅ **内容详实**: 输出内容深入且全面，非简短回答
- ✅ **结构清晰**: 答案通常包含明确的层次结构和要点
- ✅ **双语支持**: 涵盖中英文双语的网络安全知识
- ✅ **专业性强**: 覆盖从基础概念到高级技术的完整知识体系
- ✅ **实用性高**: 包含大量实战经验和工具使用场景

---

## 使用场景 | Use Cases

### 1. 大语言模型训练 | LLM Training
- 网络安全领域的指令微调（Instruction Tuning）
- 领域知识增强和模型适配
- RAG（检索增强生成）系统的知识库构建

### 2. 智能问答系统 | Intelligent QA Systems
- 网络安全智能客服机器人
- 技术支持与故障排查助手
- 学习辅导与知识问答平台

### 3. 知识图谱构建 | Knowledge Graph Construction
- 网络安全实体关系抽取
- 领域本体构建与知识推理
- 威胁情报知识库

### 4. 教育培训 | Education & Training
- 网络安全课程题库生成
- CTF（Capture The Flag）训练数据
- 认证考试备考资料（CISSP、CEH等）

### 5. 安全研究 | Security Research
- 威胁情报自动化分析
- 漏洞模式挖掘与研究
- 攻防技术知识库构建

---

## 使用方法 | Usage

### Python示例 | Python Example

```python
import json

# 读取数据集
def load_dataset(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

# 使用示例
dataset_path = 'cleaned_2026-1-5-Cybersecurity-bigDataset_qualified_qualified.jsonl'
data = load_dataset(dataset_path)

print(f"总数据条数: {len(data)}")
print(f"示例数据:\n{json.dumps(data[0], ensure_ascii=False, indent=2)}")
```

### HuggingFace Datasets加载 | Loading with HuggingFace

```python
from datasets import load_dataset

# 加载JSONL格式数据集
dataset = load_dataset('json', data_files='cleaned_2026-1-5-Cybersecurity-bigDataset_qualified_qualified.jsonl')

print(dataset)
print(dataset['train'][0])
```

### 用于微调 | Fine-tuning Example

```python
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import load_dataset

# 加载模型和数据集
model_name = "your-model-name"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

dataset = load_dataset('json', data_files='cleaned_2026-1-5-Cybersecurity-bigDataset_qualified_qualified.jsonl')

# 数据预处理
def preprocess_function(examples):
    inputs = [f"Instruction: {inst}\nOutput: {out}" for inst, out in zip(examples['instruction'], examples['output'])]
    model_inputs = tokenizer(inputs, max_length=2048, truncation=True, padding='max_length')
    model_inputs['labels'] = model_inputs['input_ids'].copy()
    return model_inputs

tokenized_dataset = dataset.map(preprocess_function, batched=True)

# 训练配置
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=4,
    save_steps=500,
)

# 开始训练
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset['train'],
)

trainer.train()
```

---

## 数据集统计 | Dataset Statistics

### 语言分布 | Language Distribution
根据数据采样分析，数据集包含：
- **中文数据**: 约60-70%
- **英文数据**: 约30-40%
- **中英混合**: 部分数据包含双语解释

### 内容长度统计 | Content Length Statistics
- **平均instruction长度**: ~200-500字符
- **平均output长度**: ~500-2000字符
- **最长单条数据**: 超过10,000字符

### 质量分数分布 | Quality Score Distribution
- 4.5-4.7分: 约40%
- 4.7-4.9分: 约45%
- 4.9-5.0分: 约15%

---

## 引用与致谢 | Citation & Acknowledgments

如果您在研究或项目中使用了本数据集，请按以下格式引用：

```bibtex
@dataset{cybersecurity_dataset_2026,
  title={Cybersecurity High-Quality Dataset: A Cleaned Chinese-English Q&A Corpus},
  author={Huancheng},
  year={2026},
  publisher={ModelScope},
  url={https://modelscope.cn/datasets/hcnote/Cybersecurity-Dataset},
  note={Cleaned using DataSanity (Quality Score ≥ 4.5)}
}
```

### 致谢 | Acknowledgments
- **原始数据集**: [Cybersecurity-Dataset @ ModelScope](https://modelscope.cn/datasets/hcnote/Cybersecurity-Dataset)
- **清洗工具**: [DataSanity](https://github.com/yangqi1309134997-coder/DataSanity) - 高质量数据清洗工具
- **版权所有**: 新疆幻城网安科技有限责任公司
- **开源作者**: 幻城 (Huancheng)

---

## 许可证 | License

本项目采用 **MIT License** 开源协议。详见 [LICENSE](LICENSE) 文件。

---

## 联系方式 | Contact

- **作者**: 幻城 (Huancheng)
- **公司**: 新疆幻城网安科技有限责任公司
- **QQ交流群**: 253193620
- **官方博客**: https://hcnote.cn
- **ModelScope**: https://modelscope.cn/datasets/hcnote/Cybersecurity-Dataset

---

## 更新日志 | Changelog

### v1.0.0 (2026-01-05)
- 初始版本发布
- 数据总量：270,271条
- 质量阈值：≥4.5分
- 文件大小：2.2GB

---

## 常见问题 | FAQ

**Q: 为什么数据集这么大？**
A: 为了提供高质量的训练数据，每条答案都经过详细撰写，包含深入的技术解释和实战经验，因此文件较大。

**Q: 可以用于商业用途吗？**
A: 本数据集采用MIT许可证，允许商业用途，但请遵守许可证条款并适当引用。

**Q: 数据会持续更新吗？**
A: 是的，我们会根据原始数据集的更新和清洗工具的改进，定期发布新版本。

**Q: 如何获取更多信息？**
A: 欢迎加入QQ交流群（253193620）或访问官方博客 https://hcnote.cn 获取最新信息。

---

**⭐ 如果这个数据集对您有帮助，请给我们一个Star！**
