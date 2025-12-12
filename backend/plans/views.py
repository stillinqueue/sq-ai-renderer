import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from renderer.floorplan import plan_to_svg, plan_to_pdf_bytes

def health(request):
    return JsonResponse({"ok": True, "service": "sq-ai-renderer"})

@csrf_exempt
def render_plan(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        import json
        body = json.loads(request.body.decode("utf-8") or "{}")
        plan = body.get("plan")
        px_per_m = int(body.get("px_per_m", 70))

        if not isinstance(plan, dict):
            return JsonResponse({"error": "Missing/invalid 'plan' object"}, status=400)

        svg = plan_to_svg(plan, px_per_m=px_per_m)
        pdf_bytes = plan_to_pdf_bytes(plan)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return JsonResponse({"svg": svg, "pdf_base64": pdf_b64})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
