from medkit.ask_engine import AskEngine


def test_routing_word_boundaries():
    # TEST: Substring bug (industrial should NOT match trial)
    assert AskEngine.route("industrial accidents") == "search"
    assert AskEngine.route("clinical trial for aspirin") == "trials"

def test_routing_multi_intent_scoring():
    # TEST: Multi-intent (trials + summary)
    # "trial" = 1, "summary" = 1. Priority is trials/explain.
    assert AskEngine.route("Summarize clinical trials") == "trials"
    
    # "drug" = 1, "warning" = 1, "summary" = 1 -> explain wins (score 2 vs 1)
    assert AskEngine.route("Summarize drug warning for aspirin") == "explain"

def test_routing_noise_cleaning():
    # TEST: clean_query preserves meaning
    query = "What is research on profit?"
    cleaned = AskEngine.clean_query(query)
    # The new clean_query should preserve "profit" and avoid destroying the core term
    assert "profit" in cleaned
    assert "what is" not in cleaned
    assert "research on" not in cleaned

def test_routing_confidence_default():
    # TEST: Junk query defaults to search
    assert AskEngine.route("hello how are you") == "search"

if __name__ == "__main__":
    print("Running Routing V1.1 Verification...")
    try:
        test_routing_word_boundaries()
        print("✅ Word boundaries verified (No substring bugs)")
        
        test_routing_multi_intent_scoring()
        print("✅ Multi-intent scoring verified")
        
        test_routing_noise_cleaning()
        print("✅ Noise cleaning verified (Non-destructive)")
        
        test_routing_confidence_default()
        print("✅ Default search verified")
        
        print("\n🏆 ALL V1.1 ROUTING FIXES VERIFIED!")
    except AssertionError as e:
        print(f"❌ Verification failed: {e}")
