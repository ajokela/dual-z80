TARGET = kz80
PCBAPP = pcb-rnd
RENAMEPCB = ../../bin/renamepcb
MYDATE = $(shell date +'%Y_%m%d_%H%M%S')

.phony: all clean gerber

all:
	lepton-sch2pcb --elements-dir "./symbols" project

sch:
	lepton-schematic $(TARGET).sch

pcb:
	$(PCBAPP) $(TARGET).pcb
	
clean:
	rm -f *.net *.cmd
	rm -rf gerbers
	rm -f *~ *- *.backup

gerber:
	mkdir -p gerbers
	cp $(TARGET).pcb gerbers/
	cd gerbers/; pcb-rnd -x gerber --all-layers $(TARGET).pcb 
	$(RENAMEPCB) gerbers
	rm ./gerbers/$(TARGET).pcb
	zip $(TARGET)_gerbers.zip gerbers/*

backup:
	mkdir -p ./archive/sch
	mkdir -p ./archive/pcb
	cp $(TARGET).sch ./archive/sch/$(TARGET)_$(MYDATE).sch
	cp $(TARGET).pcb ./archive/pcb/$(TARGET)_$(MYDATE).pcb
