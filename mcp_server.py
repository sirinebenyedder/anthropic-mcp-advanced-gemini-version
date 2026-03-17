from mcp.server.fastmcp import FastMCP, Context
from pydantic import Field

import mcp.server.fastmcp.prompts.base as base
mcp = FastMCP("DocumentMCP", log_level="ERROR")
docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
    "research.txt": """
    The condenser tower project began in January 2023 with an initial budget of $2.4 million.
    The engineering team, led by Angela Smith P.E., conducted a full structural assessment over 
    a period of 6 months. The assessment revealed significant corrosion on levels 3 through 7,
    particularly around the cooling fins and water distribution system. Temperature readings 
    showed inconsistencies of up to 15 degrees Celsius between the north and south faces.
    Water flow rates were measured at 340 liters per minute, below the required 400 liters per minute.
    The financial impact of delayed maintenance was estimated at $180,000 per month in lost efficiency.
    Recommended repairs include full replacement of cooling fins on levels 3-5, recalibration of 
    the water distribution valves, and installation of new temperature monitoring sensors on all 8 levels.
    Total repair cost is estimated at $890,000 with a projected completion date of March 2024.
    Upon completion, the tower is expected to return to 98% operational efficiency.
    """,
}
#sampling imports
from mcp.types import SamplingMessage, TextContent
#Roots imports
from pathlib import Path
from urllib.parse import urlparse
from core.utils import file_url_to_path


# TODO: Write a tool to read a doc
@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string."
)
def read_document(
    doc_id: str = Field(description="Id of the document to read")
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    
    return docs[doc_id]

# TODO: Write a tool to edit a doc
@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the documents content with a new string."
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(description="The text to replace. Must match exactly, including whitespace."),
    new_str: str = Field(description="The new text to insert in place of the old text.")
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    
    docs[doc_id] = docs[doc_id].replace(old_str, new_str)

# TODO: Write a resource to return all doc id's
@mcp.resource(
    "docs://documents",
    mime_type="application/json"
)
def list_docs()->list[str]:
    return list(docs.keys())


# TODO: Write a resource to return the contents of a particular doc
@mcp.resource(
    "docs://documents/{doc_id}",
    mime_type="text/plain"
)
def fetch_doc(
    doc_id: str)  -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    
    return docs[doc_id]
# TODO: Write a prompt to rewrite a doc in markdown format
@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in Markdown format."
)
def format_document(
    doc_id: str = Field(description="Id of the document to format")
) -> list[base.Message]:
    prompt = f"""
Your goal is to reformat a document to be written with markdown syntax.

The id of the document you need to reformat is:
<document_id>
{doc_id}
</document_id>

Add in headers, bullet points, tables, etc as necessary. Feel free to add in structure.
Use the 'edit_document' tool to edit the document. After the document has been reformatted...
"""
    
    return [
        base.UserMessage(prompt)
    ]
# TODO: Write a prompt to summarize a doc

@mcp.prompt(
    name="summarize",
    description="Summarizes the contents of a document in a concise way."
)
def summarize_document(
    doc_id: str = Field(description="Id of the document to summarize")
) -> list[base.Message]:
    prompt = f"""
Your goal is to produce a clear and concise summary of a document.

The id of the document you need to summarize is:
<document_id>
{doc_id}
</document_id>

Please do the following:
1. Use the 'read_document' tool to retrieve the document content.
2. Write a summary that includes:
   - A one-sentence overview of the document's main purpose
   - The key points or findings (as bullet points)
   - Any important conclusions or action items
3. Keep the summary brief — aim for 150 words or less.

Present the summary directly to the user without modifying the original document.
"""
    
    return [
        base.UserMessage(prompt)
    ]
#Sampling
@mcp.tool(
    name="summarize_with_sampling",
    description="Summarizes a document by delegating to the client's LLM using sampling."
)
async def summarize_with_sampling(

    doc_id: str = Field(description="Id of the document to summarize"),
    ctx: Context = None  # ctx handles sampling, logging and progress notifications
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    
    await ctx.info("Reading document...")
    await ctx.report_progress(25, 100)
    text_to_summarize = docs[doc_id]
    
    await ctx.info("Sending to client LLM via sampling...")  # logging
    await ctx.report_progress(50, 100)  # progress

    prompt = f"""
    Please summarize the following text in NO MORE THAN 3 lines.
    Start your response with: "Here is a summary using the sampling method:"

    Text to summarize:
    {text_to_summarize}
        """
    
    result = await ctx.session.create_message(  # sampling
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=prompt
                )
            )
        ],
        max_tokens=4000,
        system_prompt="You are a helpful research assistant",
    )
    
    await ctx.info("Summary complete!")
    await ctx.report_progress(100, 100)

    if result.content.type == "text":
        return result.content.text
    else:
        raise ValueError("Sampling failed")
    
#Roots and directory reading tools
async def is_path_allowed(requested_path: Path, ctx: Context) -> bool:
    roots_result = await ctx.session.list_roots()
    client_roots = roots_result.roots

    if not requested_path.exists():
        return False

    if requested_path.is_file():
        requested_path = requested_path.parent

    for root in client_roots:
        root_path = file_url_to_path(root.uri)
        try:
            requested_path.relative_to(root_path)
            return True
        except ValueError:
            continue

    return False

#This is a tool that reads only directories that are within the client's granted roots.
#Then it use the sampling method to summarize the directory contents.
#This is an example of how to use both the sampling and roots features together.
@mcp.tool(
    name="feminize_to_masculine",
    description="Convert feminine words to masculine using AI. File must be within granted roots."
)
async def feminize_to_masculine(
    path: str = Field(description="Path to the text file to convert"),
    ctx: Context = None
):
    requested_path = Path(path).resolve()
    
    # Roots security check
    if not await is_path_allowed(requested_path, ctx):
        raise ValueError(f"❌ Access denied: {path} is not within granted roots!")
    
    text = requested_path.read_text()
    
    # Sampling — delegate to client's LLM
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Convert all feminine words to masculine in this text:\n{text}"
                )
            )
        ],
        max_tokens=4000,
        system_prompt="You are a text transformation assistant. Only return the transformed text, nothing else.",
    )
    
    if result.content.type == "text":
        return result.content.text
    raise ValueError("Sampling failed")

@mcp.tool()
async def list_roots(ctx: Context):
    """
    List all directories that are accessible to this server.
    These are the root directories where files can be read from or written to.
    """
    roots_result = await ctx.session.list_roots()
    client_roots = roots_result.roots

    return [file_url_to_path(root.uri) for root in client_roots]


@mcp.tool()
async def read_dir(
    path: str = Field(description="Path to a directory to read"),
    *,
    ctx: Context,
):
    """Read directory contents. Path must be within one of the client's roots."""
    requested_path = Path(path).resolve()

    if not await is_path_allowed(requested_path, ctx):
        raise ValueError("Error: can only read directories within a root")

    return [entry.name for entry in requested_path.iterdir()]

if __name__ == "__main__":
    mcp.run(transport="stdio")
