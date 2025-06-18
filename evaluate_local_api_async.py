import os
import json
import re
import random
from tqdm import tqdm
import time
from datasets import load_dataset
import argparse
import asyncio
import aiohttp
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import threading

random.seed(12345)

@dataclass
class ProgressTracker:
    total: int
    completed: int = 0
    _lock: threading.Lock = threading.Lock()
    
    def increment(self) -> int:
        with self._lock:
            self.completed += 1
            return self.completed

async def call_api_async(
    session: aiohttp.ClientSession, 
    instruction: str, 
    inputs: str, 
    semaphore: asyncio.Semaphore,
    progress: ProgressTracker = None,
    q_id: str = None
) -> str:
    async with semaphore:
        start = time.time()
        message_text = [{"role": "user", "content": instruction + inputs}]
        payload = {
            "model": args.model_name,
            "messages": message_text,
            "max_tokens": 8192,
            "top_p": 0.95,
            "top_k": 20,
            "temperature": 0.6,
        }
        
        async with session.post(
            "http://127.0.0.1:3000/v1/chat/completions",
            headers={"Authorization": f"Bearer nokey"},
            json=payload,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"API call failed with status code {response.status}: {error_text}")
            completion = await response.json()
            result = completion["choices"][0]["message"]["content"]
            
            elapsed = time.time() - start
            if progress:
                current = progress.increment()
                print(f"Request [{current}/{progress.total}] completed in {elapsed:.1f}s{f' (q_id: {q_id})' if q_id else ''}")
            else:
                print(f"Request completed in {elapsed:.1f}s")
            return result


def load_mmlu_pro():
    dataset = load_dataset("TIGER-Lab/MMLU-Pro")
    test_df, val_df = dataset["test"], dataset["validation"]
    test_df = preprocess(test_df)
    val_df = preprocess(val_df)
    return test_df, val_df


def preprocess(test_df):
    res_df = []
    for each in test_df:
        options = []
        for opt in each["options"]:
            if opt == "N/A":
                continue
            options.append(opt)
        each["options"] = options
        res_df.append(each)
    res = {}
    for each in res_df:
        if each["category"] not in res:
            res[each["category"]] = []
        res[each["category"]].append(each)
    return res


def format_example(question, options, cot_content=""):
    if cot_content == "":
        cot_content = "Let's think step by step."
    if cot_content.startswith("A: "):
        cot_content = cot_content[3:]
    example = "Question: {}\nOptions: ".format(question)
    choice_map = "ABCDEFGHIJ"
    for i, opt in enumerate(options):
        example += "{}. {}\n".format(choice_map[i], opt)
    if cot_content == "":
        example += "Answer: "
    else:
        example += "Answer: " + cot_content + "\n\n"
    return example


def extract_answer(text):
    pattern = r"answer is \(?([A-J])\)?"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        print("1st answer extract failed\n" + text)
        return extract_again(text)


def extract_again(text):
    match = re.search(r'.*[aA]nswer:\s*([A-J])', text)
    if match:
        return match.group(1)
    else:
        return extract_final(text)


def extract_final(text):
    pattern = r"\b[A-J]\b(?!.*\b[A-J]\b)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(0)
    else:
        return None


async def process_single_question(
    session: aiohttp.ClientSession,
    single_question: Dict,
    cot_examples_dict: Dict,
    exist_result: List,
    semaphore: asyncio.Semaphore,
    progress: ProgressTracker = None
) -> Dict:
    q_id = single_question["question_id"]
    
    # Check if already processed
    for each in exist_result:
        if q_id == each["question_id"] and single_question["question"] == each["question"]:
            pred = extract_answer(each["model_outputs"])
            return {
                "question_id": q_id,
                "pred": pred,
                "model_outputs": each["model_outputs"],
                "already_existed": True,
                **single_question
            }
    
    category = single_question["category"]
    cot_examples = cot_examples_dict[category]
    question = single_question["question"]
    options = single_question["options"]
    prompt = "The following are multiple choice questions (with answers) about {}. Think step by" \
             " step and then output the answer in the format of \"The answer is (X)\" at the end.\n\n" \
        .format(category)
    for each in cot_examples:
        prompt += format_example(each["question"], each["options"], each["cot_content"])
    input_text = format_example(question, options)
    
    try:
        response = await call_api_async(session, prompt, input_text, semaphore, progress, q_id)
        response = response.replace('**', '')
        pred = extract_answer(response)
        return {
            "question_id": q_id,
            "pred": pred,
            "model_outputs": response,
            "already_existed": False,
            **single_question
        }
    except Exception as e:
        if progress:
            current = progress.increment()
            print(f"Request [{current}/{progress.total}] FAILED for question {q_id}: {e}")
        else:
            print(f"Error processing question {q_id}: {e}")
        return {
            "question_id": q_id,
            "pred": None,
            "model_outputs": None,
            "already_existed": False,
            "error": str(e),
            **single_question
        }


async def process_batch(
    questions: List[Dict],
    cot_examples_dict: Dict,
    exist_result: List,
    batch_size: int = 10,
    max_concurrent: int = 5
) -> List[Dict]:
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Count only new questions (not already processed)
    new_questions = []
    for q in questions:
        q_id = q["question_id"]
        already_exists = any(
            q_id == each["question_id"] and q["question"] == each["question"]
            for each in exist_result
        )
        if not already_exists:
            new_questions.append(q)
    
    progress = ProgressTracker(total=len(new_questions))
    print(f"\nTotal new questions to process: {len(new_questions)}")
    print(f"Skipping {len(questions) - len(new_questions)} already processed questions")
    
    async with aiohttp.ClientSession() as session:
        # Process all questions (including already processed ones for consistency)
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            print(f"\nProcessing batch {i//batch_size + 1}/{(len(questions) + batch_size - 1)//batch_size}")
            
            tasks = [
                process_single_question(session, q, cot_examples_dict, exist_result, semaphore, progress)
                for q in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
    return results


def update_result(output_res_path):
    category_record = {}
    res = []
    success = False
    while not success:
        try:
            if os.path.exists(output_res_path):
                with open(output_res_path, "r") as fi:
                    res = json.load(fi)
                    for each in res:
                        category = each["category"]
                        if category not in category_record:
                            category_record[category] = {"corr": 0.0, "wrong": 0.0}
                        if not each["pred"]:
                            x = random.randint(0, len(each["options"]) - 1)
                            if x == each["answer_index"]:
                                category_record[category]["corr"] += 1
                            else:
                                category_record[category]["wrong"] += 1
                        elif each["pred"] == each["answer"]:
                            category_record[category]["corr"] += 1
                        else:
                            category_record[category]["wrong"] += 1
            success = True
        except Exception as e:
            print("Error", e, "sleep 2 seconds")
            time.sleep(2)
    return res, category_record


def merge_results(existing_results: List[Dict], new_results: List[Dict]) -> List[Dict]:
    result_dict = {r["question_id"]: r for r in existing_results}
    
    for new_result in new_results:
        if not new_result.get("already_existed", False):
            result_dict[new_result["question_id"]] = new_result
    
    return list(result_dict.values())


def save_res(res, output_res_path):
    temp = []
    exist_q_id = []
    for each in res:
        if each["question_id"] not in exist_q_id:
            exist_q_id.append(each["question_id"])
            temp.append(each)
        else:
            continue
    res = temp
    with open(output_res_path, "w") as fo:
        fo.write(json.dumps(res))


def save_summary(category_record, output_summary_path):
    total_corr = 0.0
    total_wrong = 0.0
    for k, v in category_record.items():
        if k == "total":
            continue
        cat_acc = v["corr"] / (v["corr"] + v["wrong"])
        category_record[k]["acc"] = cat_acc
        total_corr += v["corr"]
        total_wrong += v["wrong"]
    acc = total_corr / (total_corr + total_wrong)
    category_record["total"] = {"corr": total_corr, "wrong": total_wrong, "acc": acc}
    with open(output_summary_path, "w") as fo:
        fo.write(json.dumps(category_record))


async def evaluate_async(subjects, batch_size=10, max_concurrent=5):
    test_df, dev_df = load_mmlu_pro()
    if not subjects:
        subjects = list(test_df.keys())
    print("assigned subjects", subjects)
    
    for subject in subjects:
        print(f"\n{'='*50}")
        print(f"Evaluating subject: {subject}")
        print(f"{'='*50}")
        
        test_data = test_df[subject]
        output_res_path = os.path.join(args.output_dir, subject + "_result.json")
        output_summary_path = os.path.join(args.output_dir, subject + "_summary.json")
        existing_results, category_record = update_result(output_res_path)
        
        # Process questions in batches
        start_time = time.time()
        results = await process_batch(
            test_data, 
            dev_df, 
            existing_results, 
            batch_size=batch_size,
            max_concurrent=max_concurrent
        )
        
        # Merge with existing results
        all_results = merge_results(existing_results, results)
        
        # Update category records
        category_record = {}
        for result in all_results:
            category = result["category"]
            if category not in category_record:
                category_record[category] = {"corr": 0.0, "wrong": 0.0}
            
            if result.get("pred") is None:
                category_record[category]["wrong"] += 1
            elif result["pred"] == result["answer"]:
                category_record[category]["corr"] += 1
            else:
                category_record[category]["wrong"] += 1
        
        # Save results
        save_res(all_results, output_res_path)
        save_summary(category_record, output_summary_path)
        
        elapsed_time = time.time() - start_time
        print(f"\nCompleted {subject} in {elapsed_time:.2f} seconds")
        print(f"Processed {len(results)} new questions")
        
        # Print accuracy
        if category in category_record:
            acc = category_record[category]["corr"] / (
                category_record[category]["corr"] + category_record[category]["wrong"]
            )
            print(f"Accuracy: {acc:.2%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", "-o", type=str, default="eval_results/")
    parser.add_argument("--model_name", "-m", type=str, required=True)
    parser.add_argument("--assigned_subjects", "-a", type=str, default="all")
    parser.add_argument("--batch_size", "-b", type=int, default=10, help="Number of questions to process in each batch")
    parser.add_argument("--max_concurrent", "-c", type=int, default=5, help="Maximum number of concurrent API requests")
    
    args = parser.parse_args()
    
    if args.assigned_subjects == "all":
        assigned_subjects = []
    else:
        assigned_subjects = args.assigned_subjects.split(",")
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run the async evaluation
    asyncio.run(evaluate_async(
        assigned_subjects, 
        batch_size=args.batch_size,
        max_concurrent=args.max_concurrent
    ))