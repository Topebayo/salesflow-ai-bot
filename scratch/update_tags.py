import re

with open("website/../main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Pattern for Meta API & Evolution API & trigger_ai_for_chat (where sender_name/profile_name is available or not)
# We need to be careful with indentation. We will just find the block and replace it.

def replace_block(text):
    # Find all blocks starting with `# Process real estate lead qualification tags`
    # and ending right before `# Extract [IMAGE:product_id]` or `# Send the response` (in trigger_ai_for_chat).
    
    pattern = r'(\s*)# Process real estate lead qualification tags.*?(\n\s*# Extract \[IMAGE:product_id\] tokens|# Send the response)'
    
    def replacer(match):
        indent = match.group(1)
        end_marker = match.group(2)
        
        # We need to determine if sender_name or profile_name is in scope, but we can just use a generic 'Unknown' if not accessible, or check if 'sender_name' is in the original block.
        orig_block = match.group(0)
        customer_var = "Unknown"
        if "sender_name" in orig_block:
            customer_var = "sender_name if sender_name else 'Unknown'"
        elif "profile_name" in orig_block:
            customer_var = "profile_name if profile_name else 'Unknown'"
            
        replacement = f"""{indent}# Process all AI action tags (Qualify, Orders, Inspections)
{indent}ai_response = process_ai_action_tags(business_id if 'business_id' in locals() else req.business_id, phone_number if 'phone_number' in locals() else phone, ai_response, {customer_var})
{indent}
{indent}# Check for AI-triggered handoff
{indent}if "[HANDOFF_TRIGGERED]" in ai_response:
{indent}    ai_response = ai_response.replace("[HANDOFF_TRIGGERED]", "").strip()
{indent}    db.set_human_handoff(business_id if 'business_id' in locals() else req.business_id, phone_number if 'phone_number' in locals() else phone, True)
{indent}    logger.info(f"🙋 AI triggered human handoff"){end_marker}"""
        return replacement
        
    return re.sub(pattern, replacer, text, flags=re.DOTALL)

new_content = replace_block(content)

with open("website/../main.py", "w", encoding="utf-8") as f:
    f.write(new_content)
    print("Patched main.py")
