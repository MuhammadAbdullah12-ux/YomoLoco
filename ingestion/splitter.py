import re

def count_tokens_approx(text: str) -> int:
    """
    Approximates token count based on whitespace separation and characters.
    1 token is roughly 4 characters or 0.75 words.
    """
    if not text:
        return 0
    words = text.split()
    return max(len(words), int(len(text) / 4))

def split_readme(text: str, target_min: int = 300, target_max: int = 500) -> list[str]:
    """
    Structure-aware Markdown splitter.
    1. Splits the document into sections by headers (#, ##, ###).
    2. Splits sections that exceed the maximum target size into sub-chunks.
    """
    if not text:
        return []
    
    lines = text.split("\n")
    sections = []
    current_header = ""
    current_content = []
    
    header_pattern = re.compile(r"^(#{1,6})\s+(.*)$")
    
    for line in lines:
        match = header_pattern.match(line)
        if match:
            # Save the previous section if it has content
            if current_content:
                sections.append((current_header, "\n".join(current_content)))
            current_header = line
            current_content = [line]
        else:
            current_content.append(line)
            
    # Add the last section
    if current_content:
        sections.append((current_header, "\n".join(current_content)))
        
    chunks = []
    
    for header, content in sections:
        content_str = content.strip()
        if not content_str:
            continue
            
        tokens = count_tokens_approx(content_str)
        
        # If the section fits within the target size, keep it whole
        if tokens <= target_max:
            chunks.append(content_str)
        else:
            # If it's too large, split it further by length with a small overlap
            sub_chunks = split_text_by_length(content_str, max_tokens=target_max, overlap=50)
            chunks.extend(sub_chunks)
            
    return chunks

def split_text_by_length(text: str, max_tokens: int = 500, overlap: int = 50) -> list[str]:
    """
    Splits text by token length with an overlapping window.
    Used for issues/PRs and sub-splitting oversized README sections.
    """
    if not text:
        return []
    
    # Split text into words to approximate tokens
    words = text.split()
    total_words = len(words)
    
    # If the text is small enough, return it as a single chunk
    if total_words <= max_tokens:
        return [text.strip()]
        
    chunks = []
    start_idx = 0
    step = max_tokens - overlap
    
    while start_idx < total_words:
        end_idx = min(start_idx + max_tokens, total_words)
        chunk_words = words[start_idx:end_idx]
        
        if chunk_words:
            chunks.append(" ".join(chunk_words).strip())
            
        # Break if we reached the end
        if end_idx == total_words:
            break
            
        start_idx += step
        
    return chunks
