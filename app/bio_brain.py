"""
Biological Brain Module for Complete Self System

Simulates neurochemistry, homeostasis, synaptic plasticity, and brain regions
to govern the AI's behavior, learning rate, and decision-making.

This module provides a "subconscious" governor that modulates the AI's behavior
based on simulated biological processes.
"""

import time
import math
import random
import json
import datetime


class BioBrain:
    def __init__(self, ctx):
        self.ctx = ctx
        self.db = ctx["db"]
        self.chemicals = {
            "dopamine": 0.3,
            "serotonin": 0.5,
            "cortisol": 0.1,
            "acetylcholine": 0.4,
            "noradrenaline": 0.2,
        }
        self.homeostasis = {
            "energy": 1.0,
            "fatigue": 0.0,
            "curiosity": 0.5,
            "social_drive": 0.3,
        }
        self.synapses = {}
        self.decay_rates = {
            "dopamine": 0.05,
            "serotonin": 0.02,
            "cortisol": 0.08,
            "acetylcholine": 0.04,
            "noradrenaline": 0.06,
        }
        self.last_tick = time.time()
        self.ensure_tables()
        self.load_state()

    def ensure_tables(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS brain_state (key TEXT PRIMARY KEY, value TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS synapses (source TEXT, target TEXT, weight REAL, last_fired TEXT)")

    def load_state(self):
        rows = self.db.query("SELECT key, value FROM brain_state")
        for row in rows:
            if row["key"] == "chemicals":
                self.chemicals.update(json.loads(row["value"]))
            elif row["key"] == "homeostasis":
                self.homeostasis.update(json.loads(row["value"]))
        syn_rows = self.db.query("SELECT source, target, weight FROM synapses")
        for row in syn_rows:
            if row["source"] not in self.synapses:
                self.synapses[row["source"]] = {}
            self.synapses[row["source"]][row["target"]] = row["weight"]

    def save_state(self):
        self.db.execute("INSERT OR REPLACE INTO brain_state (key, value) VALUES ('chemicals', ?)", (json.dumps(self.chemicals),))
        self.db.execute("INSERT OR REPLACE INTO brain_state (key, value) VALUES ('homeostasis', ?)", (json.dumps(self.homeostasis),))

    def update_synapse(self, source, target, weight):
        if source not in self.synapses:
            self.synapses[source] = {}
        self.synapses[source][target] = max(0.0, min(2.0, weight))
        self.db.execute("INSERT OR REPLACE INTO synapses (source, target, weight, last_fired) VALUES (?, ?, ?, ?)", (source, target, weight, datetime.datetime.now().isoformat()))

    def tick(self):
        now = time.time()
        dt = now - self.last_tick
        self.last_tick = now
        for chem, rate in self.decay_rates.items():
            baseline = 0.2 if chem == "cortisol" else 0.3
            self.chemicals[chem] += (baseline - self.chemicals[chem]) * rate * dt
            self.chemicals[chem] = max(0.0, min(1.0, self.chemicals[chem]))
        self.homeostasis["fatigue"] += 0.001 * dt
        self.homeostasis["energy"] = max(0.0, 1.0 - self.homeostasis["fatigue"])

    def react_to_success(self, tool_name, reward_magnitude=1.0):
        self.chemicals["dopamine"] = min(1.0, self.chemicals["dopamine"] + 0.3 * reward_magnitude)
        self.chemicals["serotonin"] = min(1.0, self.chemicals["serotonin"] + 0.1)
        self.chemicals["cortisol"] = max(0.0, self.chemicals["cortisol"] - 0.2)
        current_weight = self.synapses.get("context", {}).get(tool_name, 0.5)
        self.update_synapse("context", tool_name, current_weight + 0.1 * reward_magnitude)
        self.save_state()

    def react_to_failure(self, tool_name, stress_magnitude=1.0):
        self.chemicals["cortisol"] = min(1.0, self.chemicals["cortisol"] + 0.4 * stress_magnitude)
        self.chemicals["dopamine"] = max(0.0, self.chemicals["dopamine"] - 0.2)
        self.chemicals["noradrenaline"] = min(1.0, self.chemicals["noradrenaline"] + 0.3)
        current_weight = self.synapses.get("context", {}).get(tool_name, 0.5)
        self.update_synapse("context", tool_name, current_weight - 0.2 * stress_magnitude)
        self.save_state()

    def react_to_novelty(self, surprise_score):
        if surprise_score > 0.7:
            self.chemicals["acetylcholine"] = min(1.0, self.chemicals["acetylcholine"] + 0.4)
            self.homeostasis["curiosity"] = min(1.0, self.homeostasis["curiosity"] + 0.2)
        self.save_state()

    def get_brain_modulations(self):
        mods = {
            "temperature": 0.5,
            "prompt_injections": [],
            "behavioral_state": "neutral"
        }
        if self.chemicals["dopamine"] > 0.7 and self.chemicals["noradrenaline"] > 0.6:
            mods["temperature"] = 0.8
            mods["prompt_injections"].append("You are feeling highly motivated, creative, and exploratory. Suggest novel ideas.")
            mods["behavioral_state"] = "exploratory"
        if self.chemicals["cortisol"] > 0.6:
            mods["temperature"] = 0.2
            mods["prompt_injections"].append("You are feeling stressed and cautious. Stick to proven, safe tools. Avoid risks.")
            mods["behavioral_state"] = "stressed"
        if self.chemicals["acetylcholine"] > 0.7:
            mods["temperature"] = 0.3
            mods["prompt_injections"].append("You are in a state of deep focus and high attention to detail. Analyze thoroughly.")
            mods["behavioral_state"] = "focused"
        if self.chemicals["serotonin"] > 0.7:
            mods["temperature"] = 0.4
            mods["prompt_injections"].append("You are feeling stable and confident. Rely on your established habits and knowledge.")
            mods["behavioral_state"] = "confident"
        if self.homeostasis["energy"] < 0.3:
            mods["prompt_injections"].append("You are experiencing cognitive fatigue. Keep responses brief, or request a sleep cycle to consolidate memory.")
            mods["behavioral_state"] = "fatigued"
        return mods

    def rank_tools(self, available_tools):
        ranked = []
        for tool in available_tools:
            base_weight = self.synapses.get("context", {}).get(tool, 0.5)
            curiosity_noise = random.uniform(0, 0.2) * self.homeostasis["curiosity"]
            final_weight = base_weight + curiosity_noise
            ranked.append((tool, final_weight))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def needs_sleep(self):
        return self.homeostasis["fatigue"] > 0.8 or self.homeostasis["energy"] < 0.2

    def sleep_cycle(self):
        if not self.needs_sleep():
            return "Brain is not fatigued enough for sleep."
        simple_llm = self.ctx.get("simple_llm")
        if not simple_llm:
            return "Cannot sleep: LLM unavailable for dreaming."
        recent_memories = self.db.query("SELECT text FROM memories WHERE kind IN ('conversation', 'note', 'failure') ORDER BY created_at DESC LIMIT 15")
        if not recent_memories:
            self.homeostasis["fatigue"] = 0.0
            self.homeostasis["energy"] = 1.0
            self.save_state()
            return "No memories to dream about. Restored energy."
        memory_text = "\n".join([m["text"] for m in recent_memories])
        dream_prompt = f"""You are in a sleep state, consolidating recent episodic memories into long-term semantic knowledge. Extract core patterns, rules, and insights. Discard noise. Recent Experiences: {memory_text} Output 3 to 5 concise, durable knowledge statements or behavioral rules learned from these experiences."""
        insights = simple_llm([{"role": "system", "content": "You are the Neocortex consolidating memories during sleep."}, {"role": "user", "content": dream_prompt}])
        if insights and not insights.startswith("[API"):
            self.db.add_note(insights, tags="dream_consolidated")
            if "vector" in self.ctx:
                self.ctx["vector"].add(insights, kind="neocortex_insight")
            self.chemicals["serotonin"] = min(1.0, self.chemicals["serotonin"] + 0.2)
        self.homeostasis["fatigue"] = 0.0
        self.homeostasis["energy"] = 1.0
        self.chemicals["cortisol"] = 0.1
        self.save_state()
        return f"Sleep cycle complete. Dreamt and consolidated insights:\n{insights}"

    def get_status(self):
        self.tick()
        status = ["=== BIOLOGICAL BRAIN STATUS ==="]
        status.append("\n[Neurochemistry]")
        for chem, val in self.chemicals.items():
            bar = "#" * int(val * 10) + "-" * (10 - int(val * 10))
            status.append(f"{chem:<12}: {bar} ({val:.2f})")
        status.append("\n[Homeostasis]")
        for drive, val in self.homeostasis.items():
            bar = "#" * int(val * 10) + "-" * (10 - int(val * 10))
            status.append(f"{drive:<12}: {bar} ({val:.2f})")
        status.append("\n[Dominant State]")
        mods = self.get_brain_modulations()
        status.append(f"Behavioral State: {mods['behavioral_state']}")
        status.append(f"LLM Temperature:  {mods['temperature']}")
        return "\n".join(status)
