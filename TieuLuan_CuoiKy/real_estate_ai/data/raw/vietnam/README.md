# Snapshot tin rao nhà Việt Nam

Nguồn: https://huggingface.co/datasets/tinixai/vietnam-real-estates · TiniX AI · CC BY-NC 4.0.

`manifest.json` lưu revision và SHA-256 của shard gốc. `README_source.md` giữ dataset card nguồn; mô tả của nhà cung cấp có thể rộng hơn các cột thực có trong parquet. Bản thực dùng không có tọa độ.

Parquet 164 MB chỉ lưu cục bộ và bỏ qua Git. CSV nén đã lọc cho TP.HCM/Hà Nội nằm tại `artifacts/vietnam/listings_clean.csv.gz`, có checksum và nguồn trong `clean_manifest.json`. Không đưa tiêu đề/mô tả hoặc thông tin liên hệ vào artifact huấn luyện đã chia sẻ. Nhãn là giá rao bán, chưa phải giao dịch đã xác minh.
