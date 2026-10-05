FROM python:3.13-slim AS builder

WORKDIR /build

COPY requirements.txt . 

RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.13-slim AS runner

ARG OPENAI_API_KEY

WORKDIR /agent

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY agent.py server.py tool.py ./

EXPOSE 8080

# ENTRYPOINT ["python", "agent.py"]
# CMD [ "python", "agent.py" ]
CMD [ "python", "server.py" ]
