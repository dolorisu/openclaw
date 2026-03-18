#!/bin/bash
#
# Benchmark Natural - Pesan Human-like untuk WhatsApp
# Target Group: 120363406118312223@g.us
#

set -e

TARGET_GROUP="120363406118312223@g.us"
TIMEOUT=120
DELAY=15

# Pesan natural (human-like, gak terlalu teknis)
declare -a PESAN=(
    "Halo Doloris, gimana kabarnya hari ini? Udah makan belum?"
    "Coba cerita dong apa yang lagi kamu kerjain sekarang"
    "Aku butuh saran nih, menurut kamu mending mana: belajar Python atau JavaScript dulu?"
    "Test test, 123, masih aktif kan?"
    "Tau gak berita menarik hari ini? Share dong"
    "Bantu aku bikin list tugas untuk minggu ini dong"
    "Lagi sibuk gak? Mau tanya-tanya sebentar aja"
    "Doloris, kemarin kita ngobrolin apa ya? Aku lupa"
    "Rekomendasiin film yang seru dong buat nonton weekend"
    "Aku butuh semangat nih, kasih motivasi dong"
    "Coba jelasin AI itu apa dengan bahasa yang gampang dimengerti"
    "Menurut kamu hari ini cuacanya gimana?"
    "Bantu ingetin ya, besok aku ada meeting jam 10 pagi"
    "Pernah ke Bali gak? Rekomendasi tempat bagus dong"
    "Coba dong cerita lelucon receh, biar ketawa dikit"
    "Aku ada PR nih, bantu cariin info singkat ya"
    "Ini paragraf pertama.

Ini paragraf kedua, coba dipisah jadi bubble terpisah"
    "Versi OpenClaw berapa yang lagi jalan sekarang?"
    "Translate dong: Selamat pagi dunia"
    "Lagi ngapain? Cerita dong"
    "Coba tulis puisi pendek tentang kopi dan pagi"
    "Doloris, kangen nih ngobrol sama kamu"
    "Bantu hitung: 250 + 175 berapa?"
    "Kirim update progress ya kalau lagi proses sesuatu"
    "Cariin resep masakan simple buat yang baru belajar masak"
    "Kalau bisa teleport sekarang, mau ke mana?"
    "Test memory: kode favoritku adalah 42, ingetin ya"
    "Sebutin 3 hal yang bikin senang hari ini"
    "Terakhir, coba rangkum percakapan kita hari ini"
)

# Warna
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "🚀 Benchmark Natural - WhatsApp"
echo "========================================"
echo "Target: $TARGET_GROUP"
echo "Total Pesan: ${#PESAN[@]}"
echo "Timeout: ${TIMEOUT}s per pesan"
echo "Delay: ${DELAY}s antar pesan"
echo "Mulai: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# Setup PATH
export PATH="$HOME/.npm-global/bin:$PATH"

# Cek openclaw
if ! command -v openclaw &>/dev/null; then
    echo -e "${RED}❌ openclaw tidak ditemukan${NC}"
    exit 1
fi

echo -e "${GREEN}✅ OpenClaw ready${NC} (v$(openclaw --version))"
echo ""

# Cek gateway
echo "Cek gateway..."
if ! systemctl --user is-active --quiet openclaw-gateway 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Gateway belum aktif${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Gateway aktif${NC}"
echo ""

# Counter
SUCCESS=0
FAILED=0
START_TIME=$(date +%s)

# Kirim pesan
for i in "${!PESAN[@]}"; do
    NUM=$((i+1))
    MSG="${PESAN[$i]}"
    
    echo "[$NUM/${#PESAN[@]}] Kirim:"
    echo "    \"${MSG:0:60}${#MSG} ...\""
    
    # Kirim via openclaw agent
    if openclaw agent --channel whatsapp --to "$TARGET_GROUP" --timeout "$TIMEOUT" --message "$MSG" --deliver >/tmp/benchmark_${NUM}.log 2>&1; then
        echo -e "    ${GREEN}✅ Terkirim${NC}"
        ((SUCCESS++))
    else
        echo -e "    ${RED}❌ Gagal${NC}"
        echo "    Error: $(tail -1 /tmp/benchmark_${NUM}.log)"
        ((FAILED++))
    fi
    
    # Delay antar pesan
    if [ $NUM -lt ${#PESAN[@]} ]; then
        echo "    Tunggu ${DELAY}s..."
        sleep $DELAY
    fi
    echo ""
done

END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

# Ringkasan
echo "========================================"
echo "📊 Hasil Benchmark"
echo "========================================"
echo "Total Pesan: ${#PESAN[@]}"
echo -e "Berhasil: ${GREEN}$SUCCESS ✅${NC}"
echo -e "Gagal: ${RED}$FAILED ${FAILED} ❌${NC}"
echo "Success Rate: $(( SUCCESS * 100 / ${#PESAN[@]} ))%"
echo "Total Waktu: ${TOTAL_TIME}s"
echo "Selesai: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

if [ $SUCCESS -eq ${#PESAN[@]} ]; then
    echo -e "${GREEN}🎉 Perfect! Semua pesan terkirim ke WhatsApp!${NC}"
else
    echo -e "${YELLOW}⚠️  Ada $FAILED pesan gagal${NC}"
fi
