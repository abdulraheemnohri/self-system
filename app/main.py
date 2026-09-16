"""
Complete Self System - Main Entry Point

Autonomous AI agent platform with tools, plugins, and skills
"""

import os
import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import config
from app.db import db
from app.llm import llm_client, simple_llm_reply, embed_text
from app.vector_store import vector_store
from app.tools import tools
from app.agent import agent, run_agent, direct_reply


class Scheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        self.tasks = []
        self._load_tasks()
    
    def _load_tasks(self):
        scheduler_config = config.get('scheduler', {})
        enabled = scheduler_config.get('enabled', True)
        if not enabled:
            return
        tasks_config = scheduler_config.get('tasks', [])
        for task_config in tasks_config:
            self.tasks.append({
                'name': task_config.get('name', ''),
                'action': task_config.get('action', ''),
                'interval': task_config.get('interval_seconds', 3600),
                'last_run': 0,
                'enabled': True
            })
    
    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _run_loop(self):
        while self.running:
            try:
                for task in self.tasks:
                    if not task['enabled']:
                        continue
                    now = time.time()
                    if now - task['last_run'] >= task['interval']:
                        self._run_task(task)
                        task['last_run'] = now
                time.sleep(60)
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(10)
    
    def _run_task(self, task):
        action = task['action']
        try:
            if action == 'maintenance':
                db.cleanup_history(days=30)
            elif action == 'self_review':
                history = db.get_history(30)
                if history:
                    conversation = "\n".join(f"{row.get('role')}: {row.get('content')}" for row in history)
                    prompt = f"Review this conversation:\n{conversation[:7000]}"
                    messages = [{'role': 'system', 'content': 'You are an AI reviewer.'}, {'role': 'user', 'content': prompt}]
                    reply = simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
                    if reply:
                        db.add_note(reply, tags="self_review")
                        vector_store.add(reply, kind="self_review")
            elif action == 'periodic_learning':
                notes = db.list_notes(limit=20)
                if notes:
                    text = "\n".join(row.get('text', '') for row in notes)
                    prompt = f"Summarize:\n{text[:7000]}"
                    messages = [{'role': 'system', 'content': 'Summarize information.'}, {'role': 'user', 'content': prompt}]
                    reply = simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
                    if reply:
                        db.add_note(reply, tags="periodic_learning")
                        vector_store.add(reply, kind="periodic_learning")
            elif action == 'skill_proposal':
                prompt = "Propose one new plugin skill as JSON: {'name': 'skill_name', 'description': 'what it does', 'risk_level': 'low|medium|high'}"
                messages = [{'role': 'system', 'content': 'You propose skills.'}, {'role': 'user', 'content': prompt}]
                reply = simple_llm_reply(messages, max_tokens=1000, temperature=0.7)
                if reply:
                    db.add_note(reply, tags="skill_proposal")
        except Exception as e:
            print(f"Task failed: {e}")


class VoiceHandler:
    def __init__(self):
        self.enabled = config.get('voice.enabled', False)
        self.tts_available = False
        self.stt_available = False
    
    def speak(self, text: str) -> None:
        if not self.enabled or not self.tts_available:
            return
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except:
            pass
    
    def listen(self) -> str:
        if not self.enabled or not self.stt_available:
            return ""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening...")
                audio = recognizer.listen(source, timeout=10)
            return recognizer.recognize_google(audio)
        except:
            return ""


class BrowserHandler:
    def __init__(self):
        self.installed = False
        try:
            import playwright
            self.installed = True
        except:
            pass
    
    def navigate(self, url: str) -> str:
        if not self.installed:
            return "Playwright not installed"
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30000)
                title = page.title()
                browser.close()
                return title
        except Exception as e:
            return f"Error: {str(e)}"


scheduler = Scheduler()
voice = VoiceHandler()
browser = BrowserHandler()


def handle_command(command: str):
    command = command.strip()
    if command.lower() in ('/exit', 'exit', '/quit', 'quit'):
        return "__EXIT__"
    if command.lower().startswith('/config '):
        parts = command.split(' ', 3)
        if len(parts) < 2:
            return "Usage: /config <show|set|test|reset>"
        subcommand = parts[1].lower()
        if subcommand == 'show':
            if len(parts) > 2:
                return f"{parts[2]} = {config.get(parts[2])}"
            return str(config._config)
        elif subcommand == 'set':
            if len(parts) > 3:
                key, value = parts[2], parts[3]
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                config.set(key, value)
                return f"Set {key} = {value}"
            return "Usage: /config set <key> <value>"
        elif subcommand == 'test':
            health = llm_client.check_health()
            return f"LLM: {'healthy' if health.get('healthy') else 'unhealthy'}"
        elif subcommand == 'reset':
            config.reset_to_defaults()
            return "Config reset"
    if command.lower() == '/voice on':
        voice.enabled = True
        return "Voice enabled"
    if command.lower() == '/voice off':
        voice.enabled = False
        return "Voice disabled"
    if command.lower() == '/listen':
        return f"You said: {voice.listen()}"
    if command.lower().startswith('/say '):
        voice.speak(command[5:].strip())
        return f"Spoke: {command[5:]}"
    if command.lower().startswith('/browser open '):
        url = command[14:].strip()
        return f"Title: {browser.navigate(url)}" if url else "Usage: /browser open <url>"
    if command.lower() in ('/tools', 'tools'):
        return "Tools: " + ", ".join([t['name'] for t in tools.list_tools()])
    if command.lower() in ('/test', 'test'):
        return str(db.get_stats())
    if command.lower() in ('/help', 'help'):
        return "Commands: /help, /remember <k> <v>, /note <t>, /facts, /tools, /test, /exit"
    return agent.handle_command(command)


def main():
    print("=" * 60)
    print("COMPLETE SELF SYSTEM")
    print("Autonomous AI Agent Platform")
    print("=" * 60)
    print("Type /help for commands.")
    print()
    if config.get('safety.autonomous_mode', False):
        scheduler.start()
    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye.")
                scheduler.stop()
                break
            if not user_input:
                continue
            if user_input.startswith("/"):
                result = handle_command(user_input)
                if result == "__EXIT__":
                    print("Goodbye.")
                    scheduler.stop()
                    break
                if result:
                    print(f"System: {result}")
                continue
            db.add_history("user", user_input)
            reply = run_agent(user_input)
            print(f"Agent: {reply}")
            db.add_history("assistant", reply)
            vector_store.add(f"Q: {user_input}\nA: {reply}", kind='conversation')
    except KeyboardInterrupt:
        print("\nGoodbye.")
        scheduler.stop()


if __name__ == "__main__":
    main()
