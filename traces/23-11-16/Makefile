all: exp30_iso100_lv.vcd exp50_iso100_lv.vcd exp100_iso100_photo.vcd exp100_iso100_fhd.vcd exp30_iso100_fhd.vcd

%.vcd: setup1_%.wfm setup2_%.wfm convert.py setup1.yaml setup2.yaml
	python convert.py $@
