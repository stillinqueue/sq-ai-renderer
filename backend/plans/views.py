import base64
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from renderer.floorplan import plan_to_svg, plan_to_pdf_bytes

@api_view(["GET"])
def health(request):
    return Response({"ok": True, "service": "sq-ai-renderer"})

@api_view(["POST"])
def render_plan(request):
    """
    POST body:
      { "plan": { ...floorplan json... }, "px_per_m": 70 }
    Returns:
      { "svg": "<svg...>", "pdf_base64": "..." }
    """
    try:
        plan = request.data.get("plan")
        px_per_m = int(request.data.get("px_per_m", 70))

        if not isinstance(plan, dict):
            return Response({"error": "Missing/invalid 'plan' object"}, status=status.HTTP_400_BAD_REQUEST)

        svg = plan_to_svg(plan, px_per_m=px_per_m)
        pdf_bytes = plan_to_pdf_bytes(plan)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return Response({"svg": svg, "pdf_base64": pdf_b64})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
