# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'catphan_worksheet.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QSplitter,
    QVBoxLayout, QWidget)
import ui.py_ui.icons_rc

class Ui_QCatPhanWorksheet(object):
    def setupUi(self, QCatPhanWorksheet):
        if not QCatPhanWorksheet.objectName():
            QCatPhanWorksheet.setObjectName(u"QCatPhanWorksheet")
        QCatPhanWorksheet.resize(1024, 768)
        self.gridLayout = QGridLayout(QCatPhanWorksheet)
        self.gridLayout.setObjectName(u"gridLayout")
        self.mainSplitter = QSplitter(QCatPhanWorksheet)
        self.mainSplitter.setObjectName(u"mainSplitter")
        self.mainSplitter.setOrientation(Qt.Horizontal)
        self.leftFrame = QFrame(self.mainSplitter)
        self.leftFrame.setObjectName(u"leftFrame")
        self.leftFrame.setFrameShape(QFrame.StyledPanel)
        self.leftFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.leftFrame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.imageListLabel = QLabel(self.leftFrame)
        self.imageListLabel.setObjectName(u"imageListLabel")
        font = QFont()
        font.setBold(True)
        self.imageListLabel.setFont(font)

        self.verticalLayout.addWidget(self.imageListLabel)

        self.imageListWidget = QListWidget(self.leftFrame)
        self.imageListWidget.setObjectName(u"imageListWidget")
        self.imageListWidget.setSelectionMode(QListWidget.ExtendedSelection)

        self.verticalLayout.addWidget(self.imageListWidget)

        self.addImgBtn = QPushButton(self.leftFrame)
        self.addImgBtn.setObjectName(u"addImgBtn")
        icon = QIcon()
        icon.addFile(u":/colorIcons/icons/add.png", QSize(), QIcon.Normal, QIcon.Off)
        self.addImgBtn.setIcon(icon)

        self.verticalLayout.addWidget(self.addImgBtn)

        self.configGroupBox = QGroupBox(self.leftFrame)
        self.configGroupBox.setObjectName(u"configGroupBox")
        self.configGroupBox.setMinimumSize(QSize(0, 0))
        self.configFormLayout = QFormLayout(self.configGroupBox)
        self.configFormLayout.setObjectName(u"configFormLayout")
        self.configFormLayout.setLabelAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.configFormLayout.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.phantomTypeLabel = QLabel(self.configGroupBox)
        self.phantomTypeLabel.setObjectName(u"phantomTypeLabel")

        self.configFormLayout.setWidget(0, QFormLayout.LabelRole, self.phantomTypeLabel)

        self.phantomTypeCB = QComboBox(self.configGroupBox)
        self.phantomTypeCB.setObjectName(u"phantomTypeCB")

        self.configFormLayout.setWidget(0, QFormLayout.FieldRole, self.phantomTypeCB)

        self.huToleranceLabel = QLabel(self.configGroupBox)
        self.huToleranceLabel.setObjectName(u"huToleranceLabel")

        self.configFormLayout.setWidget(1, QFormLayout.LabelRole, self.huToleranceLabel)

        self.huToleranceDSB = QDoubleSpinBox(self.configGroupBox)
        self.huToleranceDSB.setObjectName(u"huToleranceDSB")
        self.huToleranceDSB.setDecimals(1)
        self.huToleranceDSB.setMaximum(100.0)
        self.huToleranceDSB.setValue(40.0)

        self.configFormLayout.setWidget(1, QFormLayout.FieldRole, self.huToleranceDSB)

        self.scalingToleranceLabel = QLabel(self.configGroupBox)
        self.scalingToleranceLabel.setObjectName(u"scalingToleranceLabel")

        self.configFormLayout.setWidget(2, QFormLayout.LabelRole, self.scalingToleranceLabel)

        self.scalingToleranceDSB = QDoubleSpinBox(self.configGroupBox)
        self.scalingToleranceDSB.setObjectName(u"scalingToleranceDSB")
        self.scalingToleranceDSB.setDecimals(3)
        self.scalingToleranceDSB.setMaximum(1.000)
        self.scalingToleranceDSB.setSingleStep(0.001)
        self.scalingToleranceDSB.setValue(0.050)

        self.configFormLayout.setWidget(2, QFormLayout.FieldRole, self.scalingToleranceDSB)

        self.lowContrastThresholdLabel = QLabel(self.configGroupBox)
        self.lowContrastThresholdLabel.setObjectName(u"lowContrastThresholdLabel")

        self.configFormLayout.setWidget(3, QFormLayout.LabelRole, self.lowContrastThresholdLabel)

        self.lowContrastThresholdDSB = QDoubleSpinBox(self.configGroupBox)
        self.lowContrastThresholdDSB.setObjectName(u"lowContrastThresholdDSB")
        self.lowContrastThresholdDSB.setDecimals(3)
        self.lowContrastThresholdDSB.setMaximum(1.000)
        self.lowContrastThresholdDSB.setSingleStep(0.001)
        self.lowContrastThresholdDSB.setValue(0.010)

        self.configFormLayout.setWidget(3, QFormLayout.FieldRole, self.lowContrastThresholdDSB)

        self.thicknessToleranceLabel = QLabel(self.configGroupBox)
        self.thicknessToleranceLabel.setObjectName(u"thicknessToleranceLabel")

        self.configFormLayout.setWidget(4, QFormLayout.LabelRole, self.thicknessToleranceLabel)

        self.thicknessToleranceDSB = QDoubleSpinBox(self.configGroupBox)
        self.thicknessToleranceDSB.setObjectName(u"thicknessToleranceDSB")
        self.thicknessToleranceDSB.setDecimals(1)
        self.thicknessToleranceDSB.setMaximum(10.0)
        self.thicknessToleranceDSB.setValue(0.2)

        self.configFormLayout.setWidget(4, QFormLayout.FieldRole, self.thicknessToleranceDSB)

        self.memoryEfficientLabel = QLabel(self.configGroupBox)
        self.memoryEfficientLabel.setObjectName(u"memoryEfficientLabel")

        self.configFormLayout.setWidget(5, QFormLayout.LabelRole, self.memoryEfficientLabel)

        self.memoryEfficientCB = QCheckBox(self.configGroupBox)
        self.memoryEfficientCB.setObjectName(u"memoryEfficientCB")

        self.configFormLayout.setWidget(5, QFormLayout.FieldRole, self.memoryEfficientCB)

        self.clearBordersLabel = QLabel(self.configGroupBox)
        self.clearBordersLabel.setObjectName(u"clearBordersLabel")

        self.configFormLayout.setWidget(6, QFormLayout.LabelRole, self.clearBordersLabel)

        self.clearBordersCB = QCheckBox(self.configGroupBox)
        self.clearBordersCB.setObjectName(u"clearBordersCB")
        self.clearBordersCB.setChecked(True)

        self.configFormLayout.setWidget(6, QFormLayout.FieldRole, self.clearBordersCB)

        self.zipAfterLabel = QLabel(self.configGroupBox)
        self.zipAfterLabel.setObjectName(u"zipAfterLabel")

        self.configFormLayout.setWidget(7, QFormLayout.LabelRole, self.zipAfterLabel)

        self.zipAfterCB = QCheckBox(self.configGroupBox)
        self.zipAfterCB.setObjectName(u"zipAfterCB")

        self.configFormLayout.setWidget(7, QFormLayout.FieldRole, self.zipAfterCB)

        self.verticalLayout.addWidget(self.configGroupBox)

        self.analyzeBtn = QPushButton(self.leftFrame)
        self.analyzeBtn.setObjectName(u"analyzeBtn")
        icon1 = QIcon()
        icon1.addFile(u":/colorIcons/icons/analyze.png", QSize(), QIcon.Normal, QIcon.Off)
        self.analyzeBtn.setIcon(icon1)

        self.verticalLayout.addWidget(self.analyzeBtn)

        self.mainSplitter.addWidget(self.leftFrame)
        self.rightFrame = QFrame(self.mainSplitter)
        self.rightFrame.setObjectName(u"rightFrame")
        self.rightFrame.setFrameShape(QFrame.StyledPanel)
        self.rightFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.rightFrame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.resultsLabel = QLabel(self.rightFrame)
        self.resultsLabel.setObjectName(u"resultsLabel")
        self.resultsLabel.setFont(font)

        self.verticalLayout_2.addWidget(self.resultsLabel)

        self.outcomeFrame = QFrame(self.rightFrame)
        self.outcomeFrame.setObjectName(u"outcomeFrame")
        self.outcomeFrame.setFrameShape(QFrame.StyledPanel)
        self.outcomeFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.outcomeFrame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.outcomeLabel = QLabel(self.outcomeFrame)
        self.outcomeLabel.setObjectName(u"outcomeLabel")
        self.outcomeLabel.setFont(font)

        self.horizontalLayout.addWidget(self.outcomeLabel)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.advancedViewBtn = QPushButton(self.outcomeFrame)
        self.advancedViewBtn.setObjectName(u"advancedViewBtn")
        icon2 = QIcon()
        icon2.addFile(u":/colorIcons/icons/advanced.png", QSize(), QIcon.Normal, QIcon.Off)
        self.advancedViewBtn.setIcon(icon2)

        self.horizontalLayout.addWidget(self.advancedViewBtn)

        self.genReportBtn = QPushButton(self.outcomeFrame)
        self.genReportBtn.setObjectName(u"genReportBtn")
        icon3 = QIcon()
        icon3.addFile(u":/colorIcons/icons/report.png", QSize(), QIcon.Normal, QIcon.Off)
        self.genReportBtn.setIcon(icon3)

        self.horizontalLayout.addWidget(self.genReportBtn)

        self.verticalLayout_2.addWidget(self.outcomeFrame)

        self.analysisInfoVL = QVBoxLayout()
        self.analysisInfoVL.setObjectName(u"analysisInfoVL")

        self.verticalLayout_2.addLayout(self.analysisInfoVL)

        self.mainSplitter.addWidget(self.rightFrame)

        self.gridLayout.addWidget(self.mainSplitter, 0, 0, 1, 1)


        self.retranslateUi(QCatPhanWorksheet)

        QMetaObject.connectSlotsByName(QCatPhanWorksheet)
    # setupUi

    def retranslateUi(self, QCatPhanWorksheet):
        QCatPhanWorksheet.setWindowTitle(QCoreApplication.translate("QCatPhanWorksheet", u"Form", None))
        self.imageListLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"CT Images", None))
        self.addImgBtn.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Add Image(s)", None))
        self.configGroupBox.setTitle(QCoreApplication.translate("QCatPhanWorksheet", u"Configuration", None))
        self.phantomTypeLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Phantom Type:", None))
        self.huToleranceLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"HU Tolerance:", None))
        self.huToleranceDSB.setSuffix(QCoreApplication.translate("QCatPhanWorksheet", u" HU", None))
        self.scalingToleranceLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Scaling Tolerance:", None))
        self.scalingToleranceDSB.setSuffix(QCoreApplication.translate("QCatPhanWorksheet", u" mm", None))
        self.lowContrastThresholdLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Low Contrast Threshold:", None))
        self.thicknessToleranceLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Thickness Tolerance:", None))
        self.thicknessToleranceDSB.setSuffix(QCoreApplication.translate("QCatPhanWorksheet", u" mm", None))
        self.memoryEfficientLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Memory Efficient Mode:", None))
        self.clearBordersLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Clear Borders:", None))
        self.zipAfterLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Zip After Analysis:", None))
        self.analyzeBtn.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Analyze", None))
        self.resultsLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Results", None))
        self.outcomeLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Analysis Outcome", None))
        self.advancedViewBtn.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Advanced View", None))
        self.genReportBtn.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Generate Report", None))
    # retranslateUi

